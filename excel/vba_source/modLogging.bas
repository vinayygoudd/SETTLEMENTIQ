Attribute VB_Name = "modLogging"
Option Explicit

Public Sub LogRunEvent(ByVal runId As String, ByVal stepName As String, ByVal statusText As String, ByVal detailsText As String)
    On Error Resume Next
    Dim wsLog As Worksheet
    Set wsLog = ThisWorkbook.Worksheets("Run_Log")
    If wsLog Is Nothing Then Exit Sub
    
    Dim nextRow As Long
    nextRow = wsLog.Cells(wsLog.Rows.Count, 1).End(xlUp).Row + 1
    wsLog.Cells(nextRow, 1).Value = "LOG_" & Format(nextRow - 5, "0000")
    wsLog.Cells(nextRow, 2).Value = runId
    wsLog.Cells(nextRow, 3).Value = Format(Now, "yyyy-mm-dd hh:nn:ss")
    wsLog.Cells(nextRow, 4).Value = stepName
    wsLog.Cells(nextRow, 5).Value = statusText
    wsLog.Cells(nextRow, 6).Value = modMain.MACRO_VERSION
    wsLog.Cells(nextRow, 7).Value = detailsText
End Sub
