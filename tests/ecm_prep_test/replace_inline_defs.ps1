# PowerShell script to replace inline definitions with imported variables
$sourceFile = "c:\Users\ylou2\Desktop\Scout\repo\scout\tests\ecm_prep_test\market_updates_test_backup.py"
$targetFile = "c:\Users\ylou2\Desktop\Scout\repo\scout\tests\ecm_prep_test\market_updates_test.py"

# Read the entire file
$content = Get-Content $sourceFile -Raw -Encoding UTF8

# Define replacements - each with start marker, end marker, and replacement text
# Line numbers from the original analysis (1-indexed)
$replacements = @(
    @{
        Start = 158
        End = 245
        Replacement = "    # Fugitive emissions for supply chain methane leakage (imported from test_data)"
    },
    @{
        Start = 609
        End = 824
        Replacement = "    # Sample refrigerant emissions measures (imported from test_data)"
    },
    @{
        Start = 842
        End = 933
        Replacement = "    # Sample exogenous HP switching rates (imported from test_data)"
    },
    @{
        Start = 954
        End = 1090
        Replacement = "    # Hard code sample fugitive refrigerant emissions input data (imported from test_data)"
    },
    @{
        Start = 1418
        End = 2185
        Replacement = "    # Sample measures definitions (imported from test_data)"
    },
    @{
        Start = 2234
        End = 2328
        Replacement = "    # Distribution measures data (imported from test_data)"
    },
    @{
        Start = 2379
        End = 2585
        Replacement = "    # Fail measures data (imported from test_data)"
    },
    @{
        Start = 2593
        End = 2748
        Replacement = "    # Warning measures data (imported from test_data)"
    },
    @{
        Start = 2753
        End = 2890
        Replacement = "    # HP measures with exogenous rates (imported from test_data)"
    },
    @{
        Start = 2891
        End = 3055
        Replacement = "    # Compete choice output (imported from test_data)"
    },
    @{
        Start = 3056
        End = 3208
        Replacement = "    # Supply-demand output (imported from test_data)"
    },
    @{
        Start = 3209
        End = 3361
        Replacement = "    # Map measures partial check microsegment output (imported from test_data)"
    },
    @{
        Start = 3362
        End = 3517
        Replacement = "    # Partial measures output (imported from test_data)"
    },
    @{
        Start = 3518
        End = 3619
        Replacement = "    # Refrigerant fugitive emissions map markets output (imported from test_data)"
    }
)

# Convert content to array of lines
$lines = $content -split "`r?`n"

# Apply replacements in reverse order to preserve line numbers
for ($i = $replacements.Count - 1; $i -ge 0; $i--) {
    $repl = $replacements[$i]
    $startIdx = $repl.Start - 1  # Convert to 0-indexed
    $endIdx = $repl.End - 1      # Convert to 0-indexed
    
    # Build new array: before + replacement + after
    if ($startIdx -eq 0) {
        $newLines = @($repl.Replacement) + $lines[($endIdx + 1)..($lines.Count - 1)]
    } elseif ($endIdx -eq ($lines.Count - 1)) {
        $newLines = $lines[0..($startIdx - 1)] + @($repl.Replacement)
    } else {
        $newLines = $lines[0..($startIdx - 1)] + @($repl.Replacement) + $lines[($endIdx + 1)..($lines.Count - 1)]
    }
    
    $lines = $newLines
}

# Save to target file
$lines | Set-Content -Path $targetFile -Encoding UTF8

Write-Host "Replacements complete. New line count: $($lines.Count)"
Write-Host "Original line count: 4410"
Write-Host "Lines removed: $(4410 - $lines.Count)"
