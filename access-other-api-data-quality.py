from ckanext.udc_import_other_portals.logic import CKANBasedImport


class DataQualityAPI(CKANBasedImport):

    def iterate_imports(self):
        """
        Override the default iterate_imports to include the quality of the package.
        """
        import requests

        for package in self.all_packages:
            # Get the quality of the package
            quality_data = (
                requests.get(
                    f"{self.base_api}/3/action/quality_show?package_id={package['id']}"
                )
                .json()
                .get("result")
            )
            
            # Add the quality to the package, we can then use this in the `map_to_cudc_package`
            if len(quality_data) > 0:
                package["quality"] = quality_data[0]

            yield package

    def map_to_cudc_package(self, src: dict, target: dict):
        """
        Map source package to cudc package.

        Args:
            src (dict): The source package that needs to be mapped.
            target (dict): The target package that imports into CUDC.
        """
        # Adding a prefix to the name to avoid potential collisions
        target["name"] = "city-toronto-" + src["name"]
        target["id"] = src["id"]
        target["title"] = src["title"]

        # Quality
        if src.get("quality"):
            score = src["quality"].get("score")
            grade = src["quality"].get("grade")
            recorded_at = src["quality"].get("recorded_at")
            
            if src.get("is_retired"):
                target["quality_annotation"] = (
                    "This dataset is retired. Its Data Quality Score will not "
                    "be calculated. The last recorded Data Quality Score was "
                    f"{float(score) * 100}% ({grade}) on {recorded_at}."
                )
            else:
                target["quality_annotation"] = (
                    f"Data Quality Score: {float(score) * 100}% ({grade}) as of {recorded_at}"
                )
            target["quality_dimension_metric"] = (
                "Data Quality is provided by the City of Toronto"
            )
            
        return target


# Define which class should be used for import, CUDC will use it as an entrypoint
DefaultImportClass = DataQualityAPI


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

    import_config = CUDCImportConfig(
        **{
            "id": str(uuid.uuid4()),
            # Organization ID, assume we are importing to an organization with ID "city-of-toronto" in CUDC
            "owner_org": "city-of-toronto",
            "platform": "ckan",
            "other_config": {
                # Test with the City of Toronto's Open Portal
                "base_api": "https://ckan0.cf.opendata.inter.prod-toronto.ca/api"
            },
        }
    )
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
