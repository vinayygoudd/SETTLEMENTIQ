Attribute VB_Name = "modUtilities"
Option Explicit

Public Function CleanIdentifier(ByVal rawVal As String) As String
    CleanIdentifier = UCase$(Trim$(rawVal))
End Function

Public Function ComputeSignedVariance(ByVal observedAmt As Double, ByVal expectedAmt As Double) As Double
    ComputeSignedVariance = Round(observedAmt - expectedAmt, 2)
End Function
