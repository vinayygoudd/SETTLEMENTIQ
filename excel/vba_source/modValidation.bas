Attribute VB_Name = "modValidation"
Option Explicit

Public Function ValidateRequiredWorksheets() As Boolean
    Dim reqSheets As Variant
    reqSheets = Array("Control_Panel", "Executive_Dashboard", "Transactions", "Settlements", _
                      "Bank_Entries", "Refunds", "Merchants", "Data_Quality", "Reconciliation", _
                      "Exception_Register", "KPI_Results", "Summary", "Run_Log", "Config", "Data_Dictionary")
    Dim sName As Variant
    Dim ws As Worksheet
    For Each sName In reqSheets
        Set ws = Nothing
        On Error Resume Next
        Set ws = ThisWorkbook.Worksheets(CStr(sName))
        On Error GoTo 0
        If ws Is Nothing Then
            ValidateRequiredWorksheets = False
            Exit Function
        End If
    Next sName
    ValidateRequiredWorksheets = True
End Function

Public Sub VerifySourceRowCountsAndControlTotals()
    On Error GoTo ValErr
    Dim wsDQ As Worksheet
    Set wsDQ = ThisWorkbook.Worksheets("Data_Quality")
    
    Dim diffInr As Double
    diffInr = CDbl(wsDQ.Range("K6").Value)
    If Abs(diffInr) > 0.005 Then
        Err.Raise vbObjectError + 202, "modValidation", "Monetary conservation difference non-zero: " & CStr(diffInr)
    End If
    
    Call modLogging.LogRunEvent(modMain.DEFAULT_RUN_ID, "VerifySourceRowCountsAndControlTotals", "COMPLETED", "Zero unexplained monetary control-total variance confirmed.")
    Exit Sub

ValErr:
    Call modLogging.LogRunEvent(modMain.DEFAULT_RUN_ID, "VerifySourceRowCountsAndControlTotals", "FAILED", Err.Description)
    Err.Raise Err.Number, Err.Source, Err.Description
End Sub
