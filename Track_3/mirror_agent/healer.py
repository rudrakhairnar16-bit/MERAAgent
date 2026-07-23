import os
import subprocess
import time
from typing import Optional


class ActionExecutor:
    def __init__(self, agent_instance=None):
        self.agent = agent_instance
        self.action_log: list[dict] = []

    def restart_container(self, container_name: str) -> dict:
        try:
            result = subprocess.run(
                ["docker", "restart", container_name],
                capture_output=True, text=True, timeout=30
            )
            success = result.returncode == 0
            action = {
                "action": "restart_container",
                "target": container_name,
                "success": success,
                "output": result.stdout.strip() if success else result.stderr.strip()
            }
            self.action_log.append(action)
            return action
        except subprocess.TimeoutExpired:
            action = {"action": "restart_container", "target": container_name, "success": False, "output": "Timeout"}
            self.action_log.append(action)
            return action
        except FileNotFoundError:
            action = {"action": "restart_container", "target": container_name, "success": False, "output": "Docker not available"}
            self.action_log.append(action)
            return action

    def tune_llm_params(self, anomaly_type: str, current_params: Optional[dict] = None) -> dict:
        if current_params is None:
            current_params = {"temperature": 0.1, "max_tokens": 2048, "model": "llama3.2:3b"}
        new_params = dict(current_params)
        action_desc = ""
        if anomaly_type == "high_latency":
            new_params["max_tokens"] = max(512, current_params.get("max_tokens", 2048) // 2)
            new_params["temperature"] = min(0.3, current_params.get("temperature", 0.1) + 0.1)
            action_desc = f"Reduced max_tokens to {new_params['max_tokens']}, increased temperature to {new_params['temperature']}"
        elif anomaly_type == "low_confidence":
            new_params["temperature"] = max(0.05, current_params.get("temperature", 0.1) - 0.05)
            action_desc = f"Reduced temperature to {new_params['temperature']} for more deterministic output"
        elif anomaly_type in ("zero_issues_suspicious", "service_down"):
            new_params["model"] = "llama3.2:3b"
            action_desc = "Reset to default model parameters"
        else:
            action_desc = "No tuning needed"
        action = {
            "action": "tune_llm_params",
            "params": new_params,
            "success": True,
            "description": action_desc
        }
        self.action_log.append(action)
        if self.agent is not None:
            self.agent.model = new_params.get("model", self.agent.model)
        return action

    def auto_retry(self, task_fn, max_attempts: int = 3, backoff: float = 1.0) -> tuple[bool, any, list]:
        results = []
        for attempt in range(1, max_attempts + 1):
            try:
                result = task_fn()
                action = {"action": "auto_retry", "attempt": attempt, "success": True}
                self.action_log.append(action)
                return True, result, [action]
            except Exception as e:
                results.append({"action": "auto_retry", "attempt": attempt, "success": False, "error": str(e)})
                if attempt < max_attempts:
                    time.sleep(backoff * attempt)
        self.action_log.extend(results)
        return False, None, results

    def apply_fix(self, anomaly: dict, container_map: Optional[dict] = None) -> dict:
        anomaly_type = anomaly.get("type", "")
        severity = anomaly.get("severity", "warning")
        if container_map is None:
            container_map = {
                "high_latency": "mera-signoz-0",
                "service_down": "mera-signoz-0",
                "low_confidence": None,
                "zero_issues_suspicious": None
            }
        fix_action: dict = {"anomaly_type": anomaly_type, "executed": False, "success": False, "improvement": 0.0}
        if anomaly_type == "high_latency":
            container = container_map.get("high_latency")
            if container and severity == "critical":
                result = self.restart_container(container)
                fix_action.update({"executed": True, "success": result["success"], "action": "restart_container", "improvement": 0.3})
            else:
                tune = self.tune_llm_params("high_latency")
                fix_action.update({"executed": True, "success": tune["success"], "action": "tune_llm_params", "improvement": 0.2})
        elif anomaly_type == "low_confidence":
            tune = self.tune_llm_params("low_confidence")
            fix_action.update({"executed": True, "success": tune["success"], "action": "tune_llm_params", "improvement": 0.15})
        elif anomaly_type == "zero_issues_suspicious":
            fix_action.update({"executed": True, "success": True, "action": "flag_for_review", "improvement": 0.1})
        elif anomaly_type == "service_down":
            container = container_map.get("service_down")
            if container:
                result = self.restart_container(container)
                fix_action.update({"executed": True, "success": result["success"], "action": "restart_container", "improvement": 0.5})
        return fix_action

    def get_summary(self) -> dict:
        total = len(self.action_log)
        successful = sum(1 for a in self.action_log if a.get("success"))
        return {"total_actions": total, "successful": successful, "failed": total - successful}
