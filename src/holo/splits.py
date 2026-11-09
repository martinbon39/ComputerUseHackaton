"""Frozen evaluation splits (decided 2026-11-07 BEFORE any patch result was seen).

DIAG_TASKS  : used for diagnostic, direction finding (seeds 0-7).
VAL         : patch selection only -> DIAG_TASKS, seeds 50-51 (never used for the final numbers).
TEST_UNSEEN : MiniWoB families never played before (final test only).
TEST_SEEN   : DIAG_TASKS with fresh seeds 100-101 (final test only).
EASY        : regression check on easy tasks, seeds 300-303.
"""
DIAG_TASKS = ("click-button-sequence,click-checkboxes,click-collapsible,click-dialog-2,click-option,click-tab,click-tab-2,"
              "click-widget,enter-password,enter-text-2,focus-text-2,login-user,login-user-popup,search-engine,"
              "use-autocomplete,social-media,click-menu,choose-list,navigate-tree,enter-date,multi-layouts,"
              "email-inbox-delete,click-checkboxes-soft,form-sequence").split(",")
VAL_SEEDS = "50-51"
TEST_UNSEEN = ["click-checkboxes-transfer", "click-checkboxes-large", "enter-time", "form-sequence-2",
               "form-sequence-3", "enter-text-dynamic", "multi-orderings", "choose-date-easy"]
TEST_UNSEEN_SEEDS = "100-104"
TEST_SEEN_SEEDS = "100-101"
EASY = ["click-button", "click-link", "enter-text"]
EASY_SEEDS = "300-303"
