#!/usr/bin/env python3
"""
Integration tests for MOKIT TUI OutputParser.
Tests the parser with realistic output files and scenarios.
"""

import sys
import unittest
from pathlib import Path
import tempfile

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mokit_tui.parser import OutputParser


class TestIntegration(unittest.TestCase):
    """Integration tests for complete scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = OutputParser()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_realistic_ch2_output(self):
        """Test with realistic CH2 calculation output"""
        content = """HF using program gaussian
%nproc=8
%mem=20gb
#p hf/x2c-tzvpall

CH2 molecule optimization

0 1
C     0.000000     0.000000     0.000000
H     0.000000     0.000000     1.089000
H     0.000000     1.026719    -0.363000

E(RHF) =       -38.88107823 a.u., <S**2>=  0.000
E(UHF) =       -38.89950060 a.u., <S**2>=  0.713
E(GVB) =       -38.93420838 a.u.
MRSF-CIS energies from GAMESS:
Ground State    0: E=    -38.892459 a.u.                        <S**2>=   0.000
Excited State   1: E=    -38.822651 a.u. (  1.90 eV), f=0.0051, <S**2>=   0.000
Excited State   2: E=    -38.695945 a.u. (  5.35 eV), f=0.0089, <S**2>=   0.000
Excited State   3: E=    -38.657460 a.u. (  6.39 eV), f=0.0000, <S**2>=   0.000
$python ch2_MRSFCIS_NO_SA-CAS.py >ch2_MRSFCIS_NO_SA-CAS.out 2>&1
CASCI energies after SA-CASSCF(0 for ground state):   E_ex/eV   fosc
State   0, E =    -38.90257869 a.u. <S**2> = 2.000
State   1, E =    -38.89244580 a.u. <S**2> = 0.000    0.276   0.0000
State   2, E =    -38.82071323 a.u. <S**2> = 0.000    2.228   0.0000
State   3, E =    -38.71285121 a.u. <S**2> = 0.000    5.163   0.0000
Warning: SCF did not converge properly
CASCI E  =       -38.90173912 a.u.
E(CASSCF) =       -38.90245513 a.u."""

        test_file = self.temp_dir / "ch2_realistic.out"
        test_file.write_text(content)

        result = self.parser.parse_output_file(str(test_file))

        # Should detect all types of information
        self.assertTrue(result["has_output"])
        self.assertEqual(len(result["programs"]), 1)  # HF using program gaussian
        self.assertEqual(len(result["warnings"]), 1)  # SCF convergence warning

        # Should find all energy entries
        self.assertEqual(
            len(result["energies"]), 14
        )  # 2 regular + 1 CASCI + 1 CASSCF + header + 4 MRSF-CIS + header + 4 SA-CAS

        energy_lines = [e["line"] for e in result["energies"]]

        # Verify specific energies are present
        energy_patterns = [
            "E(RHF)",
            "E(UHF)",
            "E(GVB)",
            "CASCI E",
            "E(CASSCF)",
            "MRSF-CIS energies from GAMESS",
            "Ground State",
            "Excited State",
            "CASCI energies after SA-CASSCF",
            "State   0, E =",
            "State   1, E =",
        ]

        for pattern in energy_patterns:
            with self.subTest(pattern=pattern):
                self.assertTrue(any(pattern in line for line in energy_lines))

    def test_multiple_sections_same_file(self):
        """Test file with multiple energy sections of the same type"""
        content = """First MRSF-CIS calculation:
MRSF-CIS energies from GAMESS:
Ground State    0: E=    -38.892459 a.u.                        <S**2>=   0.000
Excited State   1: E=    -38.822651 a.u. (  1.90 eV), f=0.0051, <S**2>=   0.000

Some intermediate calculations...

Second MRSF-CIS calculation:
MRSF-CIS energies from GAMESS:
Ground State    0: E=    -38.893459 a.u.                        <S**2>=   0.000
Excited State   1: E=    -38.823651 a.u. (  1.91 eV), f=0.0052, <S**2>=   0.000"""

        test_file = self.temp_dir / "multiple_sections.out"
        test_file.write_text(content)

        result = self.parser.parse_output_file(str(test_file))

        # Should find both MRSF-CIS sections
        self.assertEqual(len(result["energies"]), 6)  # 2 headers + 4 state lines
        energy_lines = [e["line"] for e in result["energies"]]

        # Should have two MRSF-CIS headers
        mrsf_headers = [
            line for line in energy_lines if "MRSF-CIS energies from GAMESS" in line
        ]
        self.assertEqual(len(mrsf_headers), 2)

    def test_edge_cases(self):
        """Test edge cases and unusual input"""
        test_cases = [
            # Empty file
            "",
            # File with only headers
            """MRSF-CIS energies from GAMESS:
CASCI energies after SA-CASSCF""",
            # File with headers but no states
            """MRSF-CIS energies from GAMESS:
Some other content here
CASCI energies after SA-CASSCF:
More other content""",
            # Malformed state lines
            """MRSF-CIS energies from GAMESS:
Ground State E= invalid energy
Excited State 1: E= -38.822651
State bad format""",
        ]

        for i, content in enumerate(test_cases):
            with self.subTest(test_case=i):
                test_file = self.temp_dir / f"edge_case_{i}.out"
                test_file.write_text(content)

                result = self.parser.parse_output_file(str(test_file))

                # Should not crash and should handle gracefully
                self.assertIsInstance(result, dict)
                self.assertIn("energies", result)
                self.assertIn("warnings", result)
                self.assertIn("programs", result)
                self.assertIn("has_output", result)

    def test_performance_with_large_file(self):
        """Test parser performance with large files"""
        # Create a large file with many energy entries
        lines = ["E(RHF) = -38.88107823 a.u."]

        # Add many MRSF-CIS sections
        for i in range(100):
            lines.extend(
                [
                    f"MRSF-CIS energies from GAMESS (calculation {i}):",
                    f"Ground State    0: E=    {-38.892459 - i * 0.001} a.u.",
                    f"Excited State   1: E=    {-38.822651 - i * 0.001} a.u.",
                ]
            )

        content = "\n".join(lines)
        test_file = self.temp_dir / "large_file.out"
        test_file.write_text(content)

        result = self.parser.parse_output_file(str(test_file))

        # Should handle large files correctly
        self.assertTrue(result["has_output"])
        self.assertEqual(
            len(result["energies"]), 301
        )  # 1 regular + 100 headers + 200 state lines

    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        content = """E(RHF) =       -38.88107823 a.u. ΔE=0.0
MRSF-CIS energies from GAMESS: αβ
Ground State    0: E=    -38.892459 a.u.                        <S**2>=   0.000
Excited State   1: E=    -38.822651 a.u. (  1.90 eV), f=0.0051, <S**2>=   0.000 ✓
CASCI energies after SA-CASSCF: naïve
State   0, E =    -38.90257869 a.u. <S**2> = 2.000
State   1, E =    -38.89244580 a.u. <S**2> = 0.000    0.276   0.0000"""

        test_file = self.temp_dir / "unicode.out"
        test_file.write_text(content, encoding="utf-8")

        result = self.parser.parse_output_file(str(test_file))

        # Should handle unicode correctly
        self.assertTrue(result["has_output"])
        energy_lines = [e["line"] for e in result["energies"]]

        # Check that unicode characters are preserved
        self.assertTrue(any("ΔE=0.0" in line for line in energy_lines))
        self.assertTrue(any("αβ" in line for line in energy_lines))
        self.assertTrue(any("naïve" in line for line in energy_lines))


if __name__ == "__main__":
    unittest.main()
