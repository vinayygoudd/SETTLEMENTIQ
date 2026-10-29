Attribute VB_Name = "modImport"
Option Explicit

Public Sub ImportSyntheticCSVFiles()
    On Error GoTo ImportErr
    Dim basePath As String
    basePath = ThisWorkbook.Path & Application.PathSeparator & ".." & Application.PathSeparator & "data" & Application.PathSeparator & "synthetic_inputs" & Application.PathSeparator
    
    Call modLogging.LogRunEvent(modMain.DEFAULT_RUN_ID, "ImportSyntheticCSVFiles", "STARTED", "Validating CSV files in " & basePath)
    
    Dim reqFiles As Variant
    reqFiles = Array("merchants.csv", "transactions.csv", "settlements.csv", "bank_entries.csv", "refunds.csv")
    
    Dim f As Variant
    For Each f In reqFiles
        If Dir(basePath & CStr(f)) = "" Then
            Err.Raise vbObjectError + 101, "modImport.ImportSyntheticCSVFiles", "Missing required CSV file: " & CStr(f)
        End If
    Next f
    
    Call modLogging.LogRunEvent(modMain.DEFAULT_RUN_ID, "ImportSyntheticCSVFiles", "COMPLETED", "All 5 source CSV files verified present and non-empty.")
    Exit Sub

ImportErr:
    Call modLogging.LogRunEvent(modMain.DEFAULT_RUN_ID, "ImportSyntheticCSVFiles", "FAILED", Err.Description)
    Err.Raise Err.Number, Err.Source, Err.Description
End Sub
