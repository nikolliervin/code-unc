"""Git diff operations using GitPython."""

import logging
from pathlib import Path
from typing import Optional, List, Tuple, Union
from datetime import datetime

import git
from git import Repo, InvalidGitRepositoryError, GitCommandError

from ...models.diff import GitDiff, DiffFile, ChangeType
from .parser import DiffParser


logger = logging.getLogger(__name__)


class GitDiffer:
    """Handles git diff operations and repository interactions."""
    
    def __init__(self, repo_path: Optional[Union[str, Path]] = None):
        """
        Initialize GitDiffer.
        
        Args:
            repo_path: Path to git repository. If None, uses current directory.
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self._repo: Optional[Repo] = None
        self.parser = DiffParser()
    
    @property
    def repo(self) -> Repo:
        """Get the git repository instance."""
        if self._repo is None:
            try:
                self._repo = Repo(self.repo_path, search_parent_directories=True)
            except InvalidGitRepositoryError:
                raise ValueError(f"No git repository found at {self.repo_path}")
        return self._repo
    
    def get_current_branch(self) -> str:
        """Get the name of the current branch."""
        try:
            return self.repo.active_branch.name
        except Exception:
            # Fallback for detached HEAD or other edge cases
            return "HEAD"
    
    def get_available_branches(self) -> List[str]:
        """Get list of available branches."""
        try:
            return [branch.name for branch in self.repo.branches]
        except Exception as e:
            logger.warning(f"Could not list branches: {e}")
            return []
    
    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists."""
        try:
            return branch_name in [branch.name for branch in self.repo.branches]
        except Exception:
            return False
    
    def get_commit_hash(self, ref: str = "HEAD") -> str:
        """Get commit hash for a reference."""
        try:
            return self.repo.commit(ref).hexsha
        except Exception as e:
            raise ValueError(f"Could not resolve reference '{ref}': {e}")
    
    def get_diff_between_branches(
        self,
        target_branch: str,
        source_branch: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_files: int = 50,
        ignore_whitespace: bool = True,
        ignore_binary: bool = True,
    ) -> GitDiff:
        """
        Get diff between two branches.
        
        Args:
            target_branch: Target branch to compare against
            source_branch: Source branch (defaults to current branch)
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            max_files: Maximum number of files to process
            ignore_whitespace: Whether to ignore whitespace changes
            ignore_binary: Whether to ignore binary files
            
        Returns:
            GitDiff object containing the diff data
        """
        if source_branch is None:
            source_branch = self.get_current_branch()
        
        # Validate branches exist
        if not self.branch_exists(target_branch):
            raise ValueError(f"Target branch '{target_branch}' does not exist")
        
        logger.info(f"Getting diff between {source_branch} and {target_branch}")
        
        try:
            # Get git diff
            diff_options = []
            if ignore_whitespace:
                diff_options.extend(["-w", "--ignore-all-space"])
            
            # FUCK GitPython - just use raw git commands that actually work
            if source_branch == "HEAD" or source_branch == self.get_current_branch():
                # Compare working tree with target branch
                diff_output = self.repo.git.diff(target_branch, *diff_options)
            else:
                # Compare two specific branches
                diff_output = self.repo.git.diff(target_branch, source_branch, *diff_options)
            
            # Get file list with status
            if source_branch == "HEAD" or source_branch == self.get_current_branch():
                name_status = self.repo.git.diff(target_branch, name_only=True)
            else:
                name_status = self.repo.git.diff(target_branch, source_branch, name_only=True)
            
            # Create simple diff items from file list
            diff_files = []
            processed_files = 0
            if name_status.strip():
                for file_path in name_status.strip().split('\n'):
                    if file_path.strip():
                        # Get file content for this specific file
                        try:
                            if source_branch == "HEAD" or source_branch == self.get_current_branch():
                                file_diff = self.repo.git.diff(target_branch, '--', file_path)
                            else:
                                file_diff = self.repo.git.diff(target_branch, source_branch, '--', file_path)
                            
                            # Parse this into a DiffFile directly
                            parsed_files = self.parser.parse_raw_diff(file_diff)
                            if parsed_files:
                                if isinstance(parsed_files, list):
                                    diff_files.extend(parsed_files)
                                else:
                                    # If it returns a GitDiff object, get its files
                                    diff_files.extend(parsed_files.files)
                                processed_files += 1
                            
                        except Exception as e:
                            logger.debug(f"Failed to get diff for {file_path}: {e}")
                            continue
                        
                        if processed_files >= max_files:
                            break
            
            # Create GitDiff object
            git_diff = GitDiff(
                source_branch=source_branch,
                target_branch=target_branch,
                files=diff_files,
                created_at=datetime.utcnow().isoformat(),
                repository=self._get_repo_name(),
            )
            
            # Calculate totals
            git_diff.calculate_totals()
            
            logger.info(f"Processed {len(diff_files)} files with {git_diff.total_additions} additions and {git_diff.total_deletions} deletions")
            
            return git_diff
            
        except GitCommandError as e:
            raise ValueError(f"Git command failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate diff: {e}")
    
    def get_file_content(
        self, file_path: str, ref: str = "HEAD"
    ) -> Optional[str]:
        """
        Get content of a file at a specific reference.
        
        Args:
            file_path: Path to the file
            ref: Git reference (branch, tag, commit hash)
            
        Returns:
            File content as string, or None if file doesn't exist
        """
        try:
            blob = self.repo.commit(ref).tree[file_path]
            return blob.data_stream.read().decode('utf-8')
        except Exception as e:
            logger.debug(f"Could not read {file_path} at {ref}: {e}")
            return None
    
    def _is_binary_file(self, diff_item) -> bool:
        """Check if a diff item represents a binary file."""
        try:
            # GitPython provides a binary property for diff items
            return getattr(diff_item, 'binary_file', False)
        except Exception:
            return False
    
    def _get_file_path(self, diff_item) -> str:
        """Get the file path from a diff item."""
        if diff_item.b_path:
            return diff_item.b_path
        elif diff_item.a_path:
            return diff_item.a_path
        else:
            return "unknown"
    
    def _should_include_file(
        self,
        file_path: str,
        include_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]],
    ) -> bool:
        """Check if a file should be included based on patterns."""
        import fnmatch
        
        # Check exclude patterns first
        if exclude_patterns:
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    return False
        
        # Check include patterns
        if include_patterns:
            for pattern in include_patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    return True
            return False  # No include pattern matched
        
        return True  # No patterns specified, include by default
    
    def _get_repo_name(self) -> str:
        """Get repository name from remote URL or directory name."""
        try:
            remote_url = self.repo.remotes.origin.url
            if remote_url.endswith('.git'):
                remote_url = remote_url[:-4]
            return remote_url.split('/')[-1]
        except Exception:
            return self.repo_path.name
    
    def get_uncommitted_changes(
        self,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_files: int = 50,
    ) -> GitDiff:
        """
        Get uncommitted changes in the working directory.
        
        Args:
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            max_files: Maximum number of files to process
            
        Returns:
            GitDiff object containing uncommitted changes
        """
        try:
            # Get unstaged and staged changes
            unstaged_diff = self.repo.index.diff(None)  # Working tree vs index
            staged_diff = self.repo.index.diff("HEAD")  # Index vs HEAD
            
            # Combine both diffs
            all_diffs = list(unstaged_diff) + list(staged_diff)
            
            diff_files = []
            processed_files = 0
            seen_files = set()
            
            for diff_item in all_diffs:
                if processed_files >= max_files:
                    break
                
                file_path = self._get_file_path(diff_item)
                
                # Skip duplicates (file might be in both staged and unstaged)
                if file_path in seen_files:
                    continue
                seen_files.add(file_path)
                
                # Apply filtering
                if not self._should_include_file(
                    file_path, include_patterns, exclude_patterns
                ):
                    continue
                
                try:
                    diff_file = self.parser.parse_diff_item(diff_item)
                    if diff_file:
                        diff_files.append(diff_file)
                        processed_files += 1
                except Exception as e:
                    logger.warning(f"Failed to parse diff for {file_path}: {e}")
                    continue
            
            git_diff = GitDiff(
                source_branch=self.get_current_branch(),
                target_branch="uncommitted",
                files=diff_files,
                created_at=datetime.utcnow().isoformat(),
                repository=self._get_repo_name(),
            )
            
            git_diff.calculate_totals()
            return git_diff
            
        except Exception as e:
            raise RuntimeError(f"Failed to get uncommitted changes: {e}")
    
    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        try:
            return self.repo.is_dirty(untracked_files=True)
        except Exception:
            return False 