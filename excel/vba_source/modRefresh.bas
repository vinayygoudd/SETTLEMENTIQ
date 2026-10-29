Attribute VB_Name = "modRefresh"
Option Explicit

Public Sub RefreshAllFormulasAndPivots()
    On Error GoTo RefreshErr
    Application.CalculateFull
    Dim pc As PivotCache
    For Each pc In ThisWorkbook.PivotCaches
        pc.Refresh
    Next pc
    Call modLogging.LogRunEvent(modMain.DEFAULT_RUN_ID, "RefreshAllFormulasAndPivots", "COMPLETED", "Refreshed all workbook formulas and PivotCaches.")
    Exit Sub

RefreshErr:
    Call modLogging.LogRunEvent(modMain.DEFAULT_RUN_ID, "RefreshAllFormulasAndPivots", "FAILED", Err.Description)
    Err.Raise Err.Number, Err.Source, Err.Description
End Sub
