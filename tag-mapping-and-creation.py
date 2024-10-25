from ckanext.udc_import_other_portals.logic import CKANBasedImport

class TagMappingImport(CKANBasedImport):

    def map_to_cudc_package(self, src: dict, target: dict):
        """
        Map source package to cudc package.

        Args:
            src (dict): The source package that needs to be mapped.
            target (dict): The target package that imports into CUDC.
        """
        import re
        
        # Adding a prefix to the name to avoid potential collisions
        target["name"] = "city-toronto-" + src["name"]
        target["id"] = src["id"]
        target["title"] = src["title"]
        
        # Tag Mapping Logic
        if src.get("tags"):
            # Remove special characters from tags
            tags = [re.sub(r"[^a-zA-Z0-9 ._-]", "", tag["name"]) for tag in src["tags"]]
            # Remove tags that are longer than 100 characters
            tags = [tag for tag in tags if len(tag) <= 100]
            target["tags"] = [{"name": tag} for tag in tags]

        return target

# Define which class should be used for import, CUDC will use it as an entrypoint
DefaultImportClass = TagMappingImport

# Main entry for testing
if __name__ == "__main__":
    """
    This is only local testing and ensuring that the mapping is correct
    and does not involve any actual imports to CUDC.
    It calls the external API and gets all packages and maps them to CUDC packages.

    Errors may occur when the import is:
    - missing the required fields
    - `id`/`name` already exists
    - `name` is too long
    - etc..
    """
    import uuid
    import json
    from ckanext.udc_import_other_portals.model import CUDCImportConfig
    from ckanext.udc_import_other_portals.logic.ckan_based.api import (
        get_all_packages,
    )

    import_config = CUDCImportConfig(**{
        "id": str(uuid.uuid4()),
        # Organization ID, assume we are importing to an organization with ID "city-of-toronto" in CUDC
        "owner_org": "city-of-toronto",
        "platform": "ckan",
        "other_config": {
            # Test with the City of Toronto's Open Portal
            "base_api": "https://ckan0.cf.opendata.inter.prod-toronto.ca/api"
        }
    })
    import_instance = DefaultImportClass(None, import_config, None)
    import_instance.all_packages = get_all_packages(import_instance.base_api)
    
    # Iterrate all packages
    for src in import_instance.all_packages:
        # This is the default fields assigned to the CUDC's package/catalogue entry
        target = {
            "owner_org": import_instance.import_config.owner_org,
            "type": "catalogue",
            "license_id": "notspecified",
        }
        mapped = import_instance.map_to_cudc_package(src, target)
        print("mapped", json.dumps(mapped, indent=2))
    