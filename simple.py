from ckanext.udc_import_other_portals.logic import CKANBasedImport

class ExampleSimpleImport(CKANBasedImport):

    def map_to_cudc_package(self, src: dict, target: dict):
        """
        Map source package to cudc package.

        Args:
            src (dict): The source package that needs to be mapped.
            target (dict): The target package that imports into CUDC.
        """

        # Map city of toronto -> CUDC
        package_mapping = {
            "id": "id",
            "notes": "notes", # this is the description
            "title": "title",
        }

        # One-to-one Mapping
        for src_field in package_mapping:
            if package_mapping.get(src_field) and src.get(src_field):
                target[package_mapping[src_field]] = src[src_field]
        
        # Or you can do
        # target["id"] = src["id"]
        # target["notes"] = src["notes"]
        # target["title"] = src["title"]

        # Adding a prefix to the name to avoid potential collisions
        target["name"] = "city-toronto-" + src["name"]
        return target


# Define which class should be used for import, CUDC will use it as an entrypoint
DefaultImportClass = ExampleSimpleImport


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
    

       