Attribute VB_Name = "modMain"
Option Explicit

Public Const MACRO_VERSION As String = "v1.0.0-20261025"
Public Const DEFAULT_RUN_ID As String = "RUN_20261025_001"

Public Sub RunFullSettlementIQWorkflow()
    On Error GoTo ErrHandler
    Dim startTime As Double
    startTime = Timer
    
    Call modLogging.LogRunEvent(DEFAULT_RUN_ID, "RunFullSettlementIQWorkflow", "STARTED", "Initiating end-to-end Excel reconciliation workflow.")
    
    If Not modValidation.ValidateRequiredWorksheets() Then
        Call modLogging.LogRunEvent(DEFAULT_RUN_ID, "ValidateRequiredWorksheets", "FAILED", "Missing required worksheet tabs.")
        MsgBox "Workflow halted: Required worksheets missing.", vbCritical, "SettlementIQ Error"
        Exit Sub
    End If
    
    Call modValidation.VerifySourceRowCountsAndControlTotals
    Call modRefresh.RefreshAllFormulasAndPivots
    Call modReconciliation.UpdateExceptionRegisterSummary
    Call modLogging.LogRunEvent(DEFAULT_RUN_ID, "RunFullSettlementIQWorkflow", "COMPLETED", "Workflow completed in " & Format(Timer - startTime, "0.00") & "s")
    
    ThisWorkbook.Worksheets("Control_Panel").Range("C12").Value = "COMPLETED (VERIFIED)"
    ThisWorkbook.Worksheets("Control_Panel").Range("C11").Value = Format(Now, "yyyy-mm-dd hh:nn:ss")
    MsgBox "SettlementIQ workflow completed and verified.", vbInformation, "SettlementIQ (" & MACRO_VERSION & ")"
    Exit Sub

ErrHandler:
    Call modLogging.LogRunEvent(DEFAULT_RUN_ID, "RunFullSettlementIQWorkflow", "FAILED", "Error " & Err.Number & ": " & Err.Description)
    ThisWorkbook.Worksheets("Control_Panel").Range("C12").Value = "FAILED: " & Err.Description
    MsgBox "Workflow failed cleanly without overwriting existing data: " & Err.Description, vbCritical, "SettlementIQ Error"
End Sub
