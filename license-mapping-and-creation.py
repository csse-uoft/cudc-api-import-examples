from ckanext.udc_import_other_portals.logic import CKANBasedImport

class LicenseMappingImport(CKANBasedImport):

    def map_to_cudc_package(self, src: dict, target: dict):
        """
        Map source package to cudc package.

        Args:
            src (dict): The source package that needs to be mapped.
            target (dict): The target package that imports into CUDC.
        """
        from ckanext.udc_import_other_portals.logic.base import (
            ensure_license,
        )
                
        # Adding a prefix to the name to avoid potential collisions
        target["name"] = "city-toronto-" + src["name"]
        target["id"] = src["id"]
        target["title"] = src["title"]
        
        # License Mapping Logic
        if src["license_id"] == "city-of-toronto-license":
            # This will ensure that the license id exists in CUDC
            # If it does not exist, it will create it
            ensure_license(self.build_context(), {
                "id": "city-of-toronto-license", # Should be unique, internal ID
                "title": "Open Government Licence – Toronto",
                "url": "https://open.toronto.ca/open-data-license/",
            })
            target["license_id"] = "city-of-toronto-license"
            
        # Add more license mappings here
        # ...
        
        return target

# Define which class should be used for import, CUDC will use it as an entrypoint
DefaultImportClass = LicenseMappingImport

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
    

       