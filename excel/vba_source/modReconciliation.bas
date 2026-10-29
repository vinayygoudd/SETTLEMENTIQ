Attribute VB_Name = "modReconciliation"
Option Explicit

Public Sub UpdateExceptionRegisterSummary()
    On Error GoTo ReconErr
    Application.CalculateFullRebuild
    Call modLogging.LogRunEvent(modMain.DEFAULT_RUN_ID, "UpdateExceptionRegisterSummary", "COMPLETED", "Reconciliation & Exception Register formulas recalculated.")
    Exit Sub

ReconErr:
    Call modLogging.LogRunEvent(modMain.DEFAULT_RUN_ID, "UpdateExceptionRegisterSummary", "FAILED", Err.Description)
    Err.Raise Err.Number, Err.Source, Err.Description
End Sub
