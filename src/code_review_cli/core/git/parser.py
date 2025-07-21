"""Git diff parsing utilities."""

import logging
import re
from typing import Optional, List, Union

from git.diff import Diff

from ...models.diff import (
    DiffFile, DiffHunk, DiffLine, DiffStats, ChangeType
)


logger = logging.getLogger(__name__)


class DiffParser:
    """Parses git diff output into structured data models."""
    
    def __init__(self):
        """Initialize the diff parser."""
        # Regex patterns for parsing diff headers
        self.hunk_header_pattern = re.compile(
            r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:\s+(.*))?'
        )
    
    def parse_diff_item(self, diff_item: Diff) -> Optional[DiffFile]:
        """
        Parse a GitPython Diff object into a DiffFile.
        
        Args:
            diff_item: GitPython Diff object
            
        Returns:
            DiffFile object or None if parsing fails
        """
        try:
            # Determine change type
            change_type = self._get_change_type(diff_item)
            
            # Get file paths
            old_path = diff_item.a_path if diff_item.a_path != "/dev/null" else None
            new_path = diff_item.b_path if diff_item.b_path != "/dev/null" else None
            
            # Check if binary
            is_binary = getattr(diff_item, 'binary_file', False)
            
            # Create DiffFile
            diff_file = DiffFile(
                old_path=old_path,
                new_path=new_path,
                change_type=change_type,
                binary=is_binary,
                old_mode=getattr(diff_item.a_blob, 'mode', None) if diff_item.a_blob else None,
                new_mode=getattr(diff_item.b_blob, 'mode', None) if diff_item.b_blob else None,
                old_hash=diff_item.a_blob.hexsha if diff_item.a_blob else None,
                new_hash=diff_item.b_blob.hexsha if diff_item.b_blob else None,
                stats=DiffStats(),
            )
            
            # Skip parsing hunks for binary files
            if is_binary:
                return diff_file
            
            # Parse diff content into hunks
            try:
                diff_content = diff_item.diff.decode('utf-8') if diff_item.diff else ""
                hunks = self._parse_hunks(diff_content)
                diff_file.hunks = hunks
                
                # Calculate statistics from hunks
                diff_file.calculate_stats()
                
            except UnicodeDecodeError:
                logger.warning(f"Could not decode diff content for {diff_file.path}, treating as binary")
                diff_file.binary = True
            except Exception as e:
                logger.warning(f"Failed to parse hunks for {diff_file.path}: {e}")
            
            return diff_file
            
        except Exception as e:
            logger.error(f"Failed to parse diff item: {e}")
            return None
    
    def _get_change_type(self, diff_item: Diff) -> ChangeType:
        """Determine the change type from a diff item."""
        if diff_item.new_file:
            return ChangeType.ADDED
        elif diff_item.deleted_file:
            return ChangeType.DELETED
        elif diff_item.renamed_file:
            return ChangeType.RENAMED
        elif diff_item.copied_file:
            return ChangeType.COPIED
        else:
            return ChangeType.MODIFIED
    
    def _parse_hunks(self, diff_content: str) -> List[DiffHunk]:
        """
        Parse diff content into hunks.
        
        Args:
            diff_content: Raw diff content as string
            
        Returns:
            List of DiffHunk objects
        """
        hunks = []
        lines = diff_content.split('\n')
        
        current_hunk = None
        line_idx = 0
        
        while line_idx < len(lines):
            line = lines[line_idx]
            
            # Check for hunk header
            hunk_match = self.hunk_header_pattern.match(line)
            if hunk_match:
                # Save previous hunk if exists
                if current_hunk:
                    hunks.append(current_hunk)
                
                # Parse hunk header
                old_start = int(hunk_match.group(1))
                old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
                new_start = int(hunk_match.group(3))
                new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1
                section_header = hunk_match.group(5) if hunk_match.group(5) else None
                
                current_hunk = DiffHunk(
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    section_header=section_header,
                    lines=[],
                )
                
                line_idx += 1
                continue
            
            # Process hunk content lines
            if current_hunk and line:
                diff_line = self._parse_diff_line(line, current_hunk)
                if diff_line:
                    current_hunk.lines.append(diff_line)
            
            line_idx += 1
        
        # Add the last hunk
        if current_hunk:
            hunks.append(current_hunk)
        
        return hunks
    
    def _parse_diff_line(self, line: str, hunk: DiffHunk) -> Optional[DiffLine]:
        """
        Parse a single diff line.
        
        Args:
            line: Raw diff line
            hunk: Current hunk context
            
        Returns:
            DiffLine object or None
        """
        if not line:
            return None
        
        line_type = line[0] if line else ' '
        content = line[1:] if len(line) > 1 else ''
        
        # Calculate line numbers based on hunk context and previous lines
        old_line_num = None
        new_line_num = None
        
        if line_type in [' ', '-']:  # Context or deletion
            old_line_num = self._calculate_old_line_number(hunk)
        
        if line_type in [' ', '+']:  # Context or addition
            new_line_num = self._calculate_new_line_number(hunk)
        
        return DiffLine(
            old_line_number=old_line_num,
            new_line_number=new_line_num,
            content=content,
            line_type=line_type,
        )
    
    def _calculate_old_line_number(self, hunk: DiffHunk) -> int:
        """Calculate the old line number for current position in hunk."""
        # Count context and deletion lines processed so far
        old_lines_count = sum(
            1 for line in hunk.lines 
            if line.line_type in [' ', '-']
        )
        return hunk.old_start + old_lines_count
    
    def _calculate_new_line_number(self, hunk: DiffHunk) -> int:
        """Calculate the new line number for current position in hunk."""
        # Count context and addition lines processed so far
        new_lines_count = sum(
            1 for line in hunk.lines 
            if line.line_type in [' ', '+']
        )
        return hunk.new_start + new_lines_count
    
    def parse_raw_diff(self, raw_diff: str) -> List[DiffFile]:
        """
        Parse raw git diff output into DiffFile objects.
        
        Args:
            raw_diff: Raw git diff output as string
            
        Returns:
            List of DiffFile objects
        """
        diff_files = []
        
        # Split diff into individual file sections
        file_sections = self._split_diff_by_files(raw_diff)
        
        for section in file_sections:
            try:
                diff_file = self._parse_file_section(section)
                if diff_file:
                    diff_files.append(diff_file)
            except Exception as e:
                logger.warning(f"Failed to parse file section: {e}")
                continue
        
        return diff_files
    
    def _split_diff_by_files(self, raw_diff: str) -> List[str]:
        """Split raw diff into sections for each file."""
        sections = []
        current_section = []
        
        for line in raw_diff.split('\n'):
            if line.startswith('diff --git'):
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
            current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections
    
    def _parse_file_section(self, section: str) -> Optional[DiffFile]:
        """Parse a single file's diff section."""
        lines = section.split('\n')
        if not lines:
            return None
        
        # Parse file header
        old_path = None
        new_path = None
        change_type = ChangeType.MODIFIED
        is_binary = False
        
        for line in lines:
            if line.startswith('--- '):
                old_path = line[4:].strip()
                if old_path == '/dev/null':
                    old_path = None
                    change_type = ChangeType.ADDED
            elif line.startswith('+++ '):
                new_path = line[4:].strip()
                if new_path == '/dev/null':
                    new_path = None
                    change_type = ChangeType.DELETED
            elif 'Binary files' in line:
                is_binary = True
                break
        
        if not old_path and not new_path:
            return None
        
        diff_file = DiffFile(
            old_path=old_path,
            new_path=new_path,
            change_type=change_type,
            binary=is_binary,
            stats=DiffStats(),
        )
        
        if not is_binary:
            # Find and parse hunks
            hunk_content = []
            in_hunk = False
            
            for line in lines:
                if self.hunk_header_pattern.match(line):
                    in_hunk = True
                if in_hunk:
                    hunk_content.append(line)
            
            if hunk_content:
                hunks = self._parse_hunks('\n'.join(hunk_content))
                diff_file.hunks = hunks
                diff_file.calculate_stats()
        
        return diff_file 