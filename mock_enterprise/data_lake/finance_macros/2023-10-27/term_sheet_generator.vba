Attribute VB_Name = "TermSheetGenerator"
Option Explicit

' Term Sheet Generator VBA Macro
' Last Updated: 2023-10-27
' Author: Finance Team

Sub GenerateTermSheet()
    Dim ws As Worksheet
    Dim termSheetId As String
    Dim clientId As String
    Dim amount As Double
    
    Set ws = ThisWorkbook.Sheets("Term Sheet")
    
    ' Generate term sheet ID (legacy format)
    termSheetId = "TS_" & Format(Date, "YYYYMMDD") & "_" & Format(Now, "HHMMSS")
    
    ' Get client identifier from user input
    clientId = InputBox("Enter Client ID:", "Client Information")
    
    ' Get amount
    amount = CDbl(InputBox("Enter Amount:", "Financial Details"))
    
    ' Write to worksheet
    ws.Range("A2").Value = termSheetId
    ws.Range("B2").Value = clientId
    ws.Range("C2").Value = amount
    ws.Range("D2").Value = Now()
    
    ' Log the generation
    Call LogTermSheetGeneration(termSheetId, clientId, amount)
    
    MsgBox "Term Sheet " & termSheetId & " generated successfully!", vbInformation
End Sub

Sub LogTermSheetGeneration(termSheetId As String, clientId As String, amount As Double)
    Dim logWs As Worksheet
    Set logWs = ThisWorkbook.Sheets("Log")
    
    Dim nextRow As Long
    nextRow = logWs.Cells(logWs.Rows.Count, "A").End(xlUp).Row + 1
    
    logWs.Cells(nextRow, 1).Value = termSheetId
    logWs.Cells(nextRow, 2).Value = clientId
    logWs.Cells(nextRow, 3).Value = amount
    logWs.Cells(nextRow, 4).Value = Now()
    logWs.Cells(nextRow, 5).Value = "Generated via VBA"
End Sub

' Function to validate term sheet ID format
Function IsValidTermSheetId(id As String) As Boolean
    IsValidTermSheetId = Left(id, 3) = "TS_" And Len(id) >= 12
End Function