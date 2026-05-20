"""Voice library group management (T-48).

Groups are not stored as separate entities — membership is tracked through
the ``groups`` array in each speaker's speaker.json.  Group operations
scan/update all profile files.

Rules (Spec 4.4.d–e):
- Deleting a group: remove group name from all profiles' groups arrays.
- Deleting a profile: handled by LibraryStorage.delete_profile().
- Renaming a profile: handled by LibraryStorage.rename_profile().
- A profile can be in zero or more groups.
"""

from __future__ import annotations

from library.storage import LibraryStorage


class LibraryGroups:
    """Manage group membership across all speaker profiles.

    Parameters
    ----------
    storage:
        LibraryStorage instance for the library root.
    """

    def __init__(self, storage: LibraryStorage) -> None:
        self._storage = storage

    # ------------------------------------------------------------------
    # group discovery
    # ------------------------------------------------------------------

    def list_groups(self) -> list[str]:
        """Return a sorted list of all group names currently in use."""
        groups: set[str] = set()
        for profile_path in self._storage.list_profiles():
            meta = self._storage.read_meta(profile_path.name)
            groups.update(meta.groups)
        return sorted(groups)

    def members(self, group_name: str) -> list[str]:
        """Return folder names of all profiles that belong to *group_name*."""
        result: list[str] = []
        for profile_path in self._storage.list_profiles():
            meta = self._storage.read_meta(profile_path.name)
            if group_name in meta.groups:
                result.append(profile_path.name)
        return result

    # ------------------------------------------------------------------
    # group mutation
    # ------------------------------------------------------------------

    def add_to_group(self, folder_name: str, group_name: str) -> None:
        """Add a speaker to a group.  Creates the group implicitly."""
        meta = self._storage.read_meta(folder_name)
        if group_name not in meta.groups:
            meta.groups.append(group_name)
            self._storage.write_meta(folder_name, meta)

    def remove_from_group(self, folder_name: str, group_name: str) -> None:
        """Remove a speaker from a group."""
        meta = self._storage.read_meta(folder_name)
        if group_name in meta.groups:
            meta.groups = [g for g in meta.groups if g != group_name]
            self._storage.write_meta(folder_name, meta)

    def rename_group(self, old_name: str, new_name: str) -> None:
        """Rename a group across all profiles that reference it."""
        for profile_path in self._storage.list_profiles():
            meta = self._storage.read_meta(profile_path.name)
            if old_name in meta.groups:
                meta.groups = [
                    new_name if g == old_name else g for g in meta.groups
                ]
                self._storage.write_meta(profile_path.name, meta)

    def delete_group(self, group_name: str) -> None:
        """Delete a group: remove it from all profiles that reference it."""
        for profile_path in self._storage.list_profiles():
            meta = self._storage.read_meta(profile_path.name)
            if group_name in meta.groups:
                meta.groups = [g for g in meta.groups if g != group_name]
                self._storage.write_meta(profile_path.name, meta)
