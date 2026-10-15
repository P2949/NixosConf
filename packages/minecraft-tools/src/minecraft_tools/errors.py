"""Allowlisted diagnostics shared by backup components."""


HEALTH_FAILURE_MESSAGE = "backup failed; inspect stage and service journal"



HEALTH_FAILURE_STAGES = {
    "environment-preflight", "reconciliation", "preflight", "readiness", "pending-state", "consistency-transaction", "durability-sync", "registration", "retention",
}



DIAGNOSTIC_REASONS = frozenset({
    "operation-failed", "unexpected-error", "mount-missing", "filesystem-mismatch",
    "nested-mount", "nested-subvolume", "management-unavailable", "management-incompatible",
    "snapshot-command-failed", "snapshot-timeout", "sync-command-failed", "sync-timeout",
    "btrfs-command-failed", "btrfs-timeout", "snapshot-identity-mismatch",
    "snapshot-not-readonly", "retention-integrity-failure", "metadata-invalid",
    "autosave-recovery-failed",
})



class BackupError(RuntimeError):
    def __init__(self, message, *, reason="operation-failed", stage=None):
        super().__init__(message)
        self.reason = reason if reason in DIAGNOSTIC_REASONS else "unexpected-error"
        self.stage = stage if stage in HEALTH_FAILURE_STAGES else None

