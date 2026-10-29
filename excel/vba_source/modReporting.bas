Attribute VB_Name = "modReporting"
Option Explicit

Public Sub ExportTimestampedExceptionReport()
    On Error GoTo ExportErr
    Dim ts As String
    ts = Format(Now, "yyyymmdd_hhnnss")
    Dim outPath As String
    outPath = ThisWorkbook.Path & Application.PathSeparator & ".." & Application.PathSeparator & "outputs" & Application.PathSeparator & "reports" & Application.PathSeparator & "Exception_Export_" & ts & ".pdf"
    
    ThisWorkbook.Worksheets("Exception_Register").ExportAsFixedFormat Type:=xlTypePDF, Filename:=outPath, Quality:=xlQualityStandard
    Call modLogging.LogRunEvent(modMain.DEFAULT_RUN_ID, "ExportTimestampedExceptionReport", "COMPLETED", "Exported PDF report to " & outPath)
    Exit Sub

ExportErr:
    Call modLogging.LogRunEvent(modMain.DEFAULT_RUN_ID, "ExportTimestampedExceptionReport", "FAILED", Err.Description)
    MsgBox "Export failed: " & Err.Description, vbExclamation, "SettlementIQ Export"
End Sub
