#!/usr/bin/env python3
"""
Test suite for MOKIT TUI OutputParser energy functionality.
Tests the updated energy parsing for MRSF-CIS and SA-CAS formats with headers.
"""

import sys
import unittest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mokit_tui.parser import OutputParser


class TestEnergyParsing(unittest.TestCase):
    """Test energy parsing functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = OutputParser()

    def test_mrsf_cis_header_detection(self):
        """Test MRSF-CIS section header detection"""
        header_lines = [
            "MRSF-CIS energies from GAMESS:",
            "MRSF-CIS energies from GAMESS:",
        ]

        for line in header_lines:
            with self.subTest(line=line):
                self.assertTrue(self.parser._is_energy_section_header(line))
                self.assertEqual(self.parser._get_energy_section_type(line), "mrsf_cis")

    def test_sa_cas_header_detection(self):
        """Test SA-CAS section header detection"""
        header_lines = [
            "CASCI energies after SA-CASSCF(0 for ground state):   E_ex/eV   fosc",
            "CASCI energies after SA-CASSCF",
        ]

        for line in header_lines:
            with self.subTest(line=line):
                self.assertTrue(self.parser._is_energy_section_header(line))
                self.assertEqual(self.parser._get_energy_section_type(line), "sa_cas")

    def test_mrsf_cis_state_parsing(self):
        """Test MRSF-CIS state line parsing"""
        lines = [
            "MRSF-CIS energies from GAMESS:",
            "Ground State    0: E=    -38.892459 a.u.                        <S**2>=   0.000",
            "Excited State   1: E=    -38.822651 a.u. (  1.90 eV), f=0.0051, <S**2>=   0.000",
            "Excited State   2: E=    -38.695945 a.u. (  5.35 eV), f=0.0089, <S**2>=   0.000",
            "Excited State   3: E=    -38.657460 a.u. (  6.39 eV), f=0.0000, <S**2>=   0.000",
        ]

        # Parse the section
        self.parser._parse_mrsf_cis_section(lines, 0, 1)

        # Should have 5 entries (header + 4 states)
        self.assertEqual(len(self.parser.energies), 5)

        # Check header
        self.assertEqual(
            self.parser.energies[0]["line"], "MRSF-CIS energies from GAMESS:"
        )
        self.assertEqual(self.parser.energies[0]["line_number"], 1)

        # Check states
        self.assertIn("Ground State", self.parser.energies[1]["line"])
        self.assertIn("Excited State", self.parser.energies[2]["line"])
        self.assertIn("Excited State", self.parser.energies[3]["line"])
        self.assertIn("Excited State", self.parser.energies[4]["line"])

    def test_sa_cas_state_parsing(self):
        """Test SA-CAS state line parsing"""
        lines = [
            "CASCI energies after SA-CASSCF(0 for ground state):   E_ex/eV   fosc",
            "State   0, E =    -38.90257869 a.u. <S**2> = 2.000",
            "State   1, E =    -38.89244580 a.u. <S**2> = 0.000    0.276   0.0000",
            "State   2, E =    -38.82071323 a.u. <S**2> = 0.000    2.228   0.0000",
            "State   3, E =    -38.71285121 a.u. <S**2> = 0.000    5.163   0.0000",
        ]

        # Parse the section
        self.parser._parse_sa_cas_section(lines, 0, 1)

        # Should have 5 entries (header + 4 states)
        self.assertEqual(len(self.parser.energies), 5)

        # Check header
        self.assertIn("CASCI energies after SA-CASSCF", self.parser.energies[0]["line"])
        self.assertEqual(self.parser.energies[0]["line_number"], 1)

        # Check states
        for i in range(1, 5):
            self.assertIn("State", self.parser.energies[i]["line"])
            self.assertIn("E =", self.parser.energies[i]["line"])

    def test_complete_file_parsing(self):
        """Test complete file parsing with mixed energy formats"""
        test_content = """E(RHF) =       -38.88107823 a.u., <S**2>=  0.000
E(UHF) =       -38.89950060 a.u., <S**2>=  0.713
MRSF-CIS energies from GAMESS:
Ground State    0: E=    -38.892459 a.u.                        <S**2>=   0.000
Excited State   1: E=    -38.822651 a.u. (  1.90 eV), f=0.0051, <S**2>=   0.000
Some other content
CASCI energies after SA-CASSCF(0 for ground state):   E_ex/eV   fosc
State   0, E =    -38.90257869 a.u. <S**2> = 2.000
State   1, E =    -38.89244580 a.u. <S**2> = 0.000    0.276   0.0000"""

        # Write test file
        test_file = Path(__file__).parent / "test_output.txt"
        test_file.write_text(test_content)

        try:
            # Parse the file
            result = self.parser.parse_output_file(str(test_file))

            # Should have 2 regular energies + header + 2 MRSF-CIS states + header + 2 SA-CAS states = 8 total
            self.assertEqual(len(result["energies"]), 8)
            self.assertTrue(result["has_output"])

            # Check that we have the right mix
            energy_lines = [e["line"] for e in result["energies"]]

            # Regular energies
            self.assertTrue(any("E(RHF)" in line for line in energy_lines))
            self.assertTrue(any("E(UHF)" in line for line in energy_lines))

            # MRSF-CIS header and states
            self.assertTrue(
                any("MRSF-CIS energies from GAMESS" in line for line in energy_lines)
            )
            self.assertTrue(any("Ground State" in line for line in energy_lines))
            self.assertTrue(any("Excited State" in line for line in energy_lines))

            # SA-CAS header and states
            self.assertTrue(
                any("CASCI energies after SA-CASSCF" in line for line in energy_lines)
            )
            self.assertTrue(any("State   0, E =" in line for line in energy_lines))
            self.assertTrue(any("State   1, E =" in line for line in energy_lines))

        finally:
            # Clean up
            test_file.unlink(missing_ok=True)

    def test_no_energy_output(self):
        """Test parsing file with no energy information"""
        test_content = """Some random content
No energies here
Just plain text without any energy patterns"""
        
        # Write test file
        test_file = Path(__file__).parent / "test_no_energy.txt"
        test_file.write_text(test_content)
        
        try:
            result = self.parser.parse_output_file(str(test_file))
            
            self.assertEqual(len(result["energies"]), 0)
            self.assertFalse(result["has_output"])
            
        finally:
            test_file.unlink(missing_ok=True)

    def test_unknown_section_type(self):
        """Test handling of unknown section types"""
        line = "Unknown section header"
        result = self.parser._get_energy_section_type(line)
        self.assertEqual(result, "unknown")

    def test_non_section_lines(self):
        """Test that non-section lines are not detected as headers"""
        non_header_lines = [
            "Regular energy line",
            "Warning: Something went wrong",
            "Using program gaussian",
            "Random content",
            "Ground State (not in section)",
        ]

        for line in non_header_lines:
            with self.subTest(line=line):
                self.assertFalse(self.parser._is_energy_section_header(line))


class TestEnergyFormatting(unittest.TestCase):
    """Test energy output formatting"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = OutputParser()

    def test_format_preview_with_headers(self):
        """Test that headers are included in formatted preview"""
        test_data = {
            "has_output": True,
            "energies": [
                {"line": "MRSF-CIS energies from GAMESS:", "line_number": 1},
                {"line": "Ground State    0: E=    -38.892459 a.u.", "line_number": 2},
                {"line": "Excited State   1: E=    -38.822651 a.u.", "line_number": 3},
                {"line": "CASCI energies after SA-CASSCF:", "line_number": 5},
                {"line": "State   0, E =    -38.90257869 a.u.", "line_number": 6},
            ],
            "warnings": [],
            "programs": [],
        }

        formatted = self.parser.format_preview(test_data)

        # Should contain header labels
        self.assertIn("Energies:", formatted)

        # Should contain our specific energy lines
        self.assertIn("MRSF-CIS energies from GAMESS:", formatted)
        self.assertIn("Ground State", formatted)
        self.assertIn("CASCI energies after SA-CASSCF", formatted)
        self.assertIn("State   0", formatted)


if __name__ == "__main__":
    unittest.main()
