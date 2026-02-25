"""DecisionSession: a pausable, resumable state machine for the decision pipeline.

The session is UI-agnostic: step() does no IO. It runs one agent, returns a
StepResult telling the caller what happened and what user action is needed.
CLI and Web adapters both call the same step() method.
"""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .agents import run_agent, LIUBU
from .llm import deep_get, DEFAULT_MODEL
from .renderer import build_markdown

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

ACTIONS = {
    "select_draft": "用户选择偏好草案",
    "review_opinion": "用户审阅审议意见",
    "confirm_final": "用户确认圣裁定稿",
    "confirm_dept": "用户确认部门输出",
    "done": "流程结束",
}


@dataclass
class StepResult:
    agent_label: str
    data: dict
    action: str
    choices: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------

STATE_DRAFT = "draft"
STATE_REVIEW = "review"
STATE_FINAL = "final"
STATE_DEPT = "dept"
STATE_DONE = "done"

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class DecisionSession:
    def __init__(self, issue: dict, model: str, api_key: str, outdir: str):
        self.issue = issue
        self.model = model
        self.api_key = api_key
        self.outdir = outdir

        self.state = STATE_DRAFT
        self.draft: Optional[dict] = None
        self.review: Optional[dict] = None
        self.final: Optional[dict] = None
        self.liubu: dict = {}
        self.dept_index = 0
        self.user_opinions: dict = {}
        self.history: list = []

        os.makedirs(outdir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def step(self, user_input: Optional[dict] = None) -> StepResult:
        """Execute one pipeline step. Returns a StepResult.

        user_input format varies by action:
          select_draft  -> {"choice": 1, "comment": "..."} or None/{}
          review_opinion -> {"action": "approve"} | {"action": "comment", "comment": "..."} | {"action": "reject"}
          confirm_final -> {"action": "approve"} | {"action": "reject_to_review"} | {"action": "reject_to_draft"}
          confirm_dept  -> {"action": "approve"} | {"action": "redo", "comment": "..."}
        """
        if self.state == STATE_DRAFT:
            return self._step_draft(user_input)
        if self.state == STATE_REVIEW:
            return self._step_review(user_input)
        if self.state == STATE_FINAL:
            return self._step_final(user_input)
        if self.state == STATE_DEPT:
            return self._step_dept(user_input)
        return StepResult(agent_label="", data={}, action="done")

    def generate_report(self) -> str:
        exec_plan = {
            "issue_id": self.final.get("issue_id", self.draft.get("issue_id", "")),
            "liubu": self.liubu,
        }
        self._save("exec_plan.json", exec_plan)
        md = build_markdown(self.issue, self.draft, self.review, self.final, exec_plan)
        md_path = os.path.join(self.outdir, "decision.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        return md_path

    # ------------------------------------------------------------------
    # Checkpoint
    # ------------------------------------------------------------------

    def save_checkpoint(self):
        data = {
            "issue": self.issue,
            "model": self.model,
            "outdir": self.outdir,
            "state": self.state,
            "draft": self.draft,
            "review": self.review,
            "final": self.final,
            "liubu": self.liubu,
            "dept_index": self.dept_index,
            "user_opinions": self.user_opinions,
            "history": self.history,
        }
        self._save("checkpoint.json", data)

    @classmethod
    def load_checkpoint(cls, path: str, api_key: str) -> "DecisionSession":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        s = cls(data["issue"], data["model"], api_key, data["outdir"])
        s.state = data["state"]
        s.draft = data.get("draft")
        s.review = data.get("review")
        s.final = data.get("final")
        s.liubu = data.get("liubu", {})
        s.dept_index = data.get("dept_index", 0)
        s.user_opinions = data.get("user_opinions", {})
        s.history = data.get("history", [])
        return s

    # ------------------------------------------------------------------
    # Private: state handlers
    # ------------------------------------------------------------------

    def _step_draft(self, user_input):
        if self.draft is None:
            self.draft = self._run("zhongshu.md", self.issue, "中书省·草案")
            self._save("01_zhongshu_draft.json", self.draft)
            return StepResult(
                agent_label="中书省·草案",
                data=self.draft,
                action="select_draft",
                choices=self._draft_choices(),
            )

        # user_input contains draft preference
        ui = user_input or {}
        if ui.get("choice") or ui.get("comment"):
            self.user_opinions["draft_preference"] = ui
        self.state = STATE_REVIEW
        self.review = None
        return self._step_review(None)

    def _step_review(self, user_input):
        if self.review is None:
            review_input = dict(self.draft)
            pref = self.user_opinions.get("draft_preference")
            if pref:
                review_input["user_preference"] = pref
            self.review = self._run("menxia.md", review_input, "门下省·审议")
            self._save("02_menxia_review.json", self.review)
            return StepResult(
                agent_label="门下省·审议",
                data=self.review,
                action="review_opinion",
                choices=["approve", "comment", "reject"],
            )

        ui = user_input or {}
        action = ui.get("action", "approve")
        if action == "reject":
            self.draft = None
            self.review = None
            self.state = STATE_DRAFT
            return self._step_draft(None)
        if action == "comment":
            self.user_opinions["review_comment"] = ui.get("comment", "")
        self.state = STATE_FINAL
        self.final = None
        return self._step_final(None)

    def _step_final(self, user_input):
        if self.final is None:
            final_input = {"Draft": self.draft, "Review": self.review}
            review_comment = self.user_opinions.get("review_comment")
            if review_comment:
                final_input["user_opinion"] = review_comment
            self.final = self._run("shangshu.md", final_input, "尚书省·定稿")
            self._save("03_shangshu_final.json", self.final)
            return StepResult(
                agent_label="尚书省·定稿",
                data=self.final,
                action="confirm_final",
                choices=["approve", "reject_to_review", "reject_to_draft"],
            )

        ui = user_input or {}
        action = ui.get("action", "approve")
        if action == "reject_to_draft":
            self.draft = None
            self.review = None
            self.final = None
            self.state = STATE_DRAFT
            return self._step_draft(None)
        if action == "reject_to_review":
            self.review = None
            self.final = None
            self.state = STATE_REVIEW
            return self._step_review(None)
        self.state = STATE_DEPT
        self.dept_index = 0
        self.liubu = {}
        return self._step_dept(None)

    def _step_dept(self, user_input):
        dept_cfg = LIUBU[self.dept_index]
        key = dept_cfg["key"]
        label = dept_cfg["label"]

        if key not in self.liubu:
            dept_input = dict(self.final)
            feedback = self.user_opinions.get(f"dept_{key}_feedback")
            if feedback:
                dept_input["user_feedback"] = feedback
            result = self._run(dept_cfg["file"], dept_input, label)
            self.liubu[key] = result
            self._save(f"{dept_cfg['seq']:02d}_{key}.json", result)
            return StepResult(
                agent_label=label,
                data=result,
                action="confirm_dept",
                choices=["approve", "redo"],
            )

        ui = user_input or {}
        action = ui.get("action", "approve")
        if action == "redo":
            self.user_opinions[f"dept_{key}_feedback"] = ui.get("comment", "")
            del self.liubu[key]
            return self._step_dept(None)

        self.dept_index += 1
        if self.dept_index >= len(LIUBU):
            self.state = STATE_DONE
            md_path = self.generate_report()
            return StepResult(
                agent_label="完成",
                data={"report_path": md_path},
                action="done",
            )
        return self._step_dept(None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run(self, prompt_file, input_obj, label):
        self.history.append({"agent": label, "timestamp": datetime.now().isoformat()})
        return run_agent(prompt_file, input_obj, self.model, self.api_key)

    def _save(self, filename, data):
        path = os.path.join(self.outdir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _draft_choices(self):
        drafts = deep_get(self.draft, "drafts", "options", "plans", default=[])
        choices = []
        for i, opt in enumerate(drafts, 1):
            name = deep_get(opt, "name", "title", "summary", default=f"方案{i}")
            choices.append({"index": i, "name": name})
        return choices
