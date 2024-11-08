# Install packages/toolkit for testing and getting suggestions from IDE

## Prepare virtual environment (Windows)
```
py -m venv .venv
.venv\Scripts\activate
```

## Prepare virtual environment (Unix/macOS)
```
python3 -m venv .venv
source .venv/bin/activate
```

## Install packages
```
pip install 'git+https://github.com/ckan/ckan.git#egg=ckan[requirements,dev]'
pip install 'git+https://github.com/csse-uoft/ckanext-udc.git#egg=ckanext-udc[requirements,dev]'
pip install socketio python-magic-bin
```

# Introduction to API Import (From CKAN based portal)


## Getting familiar with the [maturity model](https://github.com/csse-uoft/ckanext-udc/blob/main/ckanext/udc/config.example.json#L12)

## CUDC Package/Catalogue Entry Fields
- id (string) - the package ID, usually UUID
- name (string) – the name of the new package, must be between 2 and 100 characters long and contain - only lowercase alphanumeric characters, - and _, e.g. 'warandpeace'. The name is used within an URL
- owner_org (organization id/name) - the organization that this package belongs to
- title (string) – the title of the package (optional, default: same as name)
- author (string) – the name of the package's author (optional)
- author_email (string) – the email address of the package's author (optional)
- license_id (license id string) – the id of the package's license
- notes (string) – a description of the package (optional)
- url (string) – a URL for the package's source (optional)


## CKAN API endpoints

### [`/api/3/action/package_show?id=<ID or Name>`](https://docs.ckan.org/en/2.11/api/index.html#ckan.logic.action.get.package_show)
Getting package with name/id `house-prices-and-affordability` from https://data.urbandatacentre.ca
```
https://data.urbandatacentre.ca/api/3/action/package_show?id=house-prices-and-affordability
```
Getting package with name/id `road-restrictions` from https://ckan0.cf.opendata.inter.prod-toronto.ca/
```
https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show?id=road-restrictions
```

## Examples
### Simple Import (title+name+id+description)
> See [simply.py](./simple.py)

The code snippets includes
- a class `ExampleSimpleImport` that extends [`CKANBasedImport`](https://github.com/csse-uoft/ckanext-udc/blob/main/ckanext/udc_import_other_portals/logic/ckan_based/base.py#L17)
- a single method `map_to_cudc_package` that will be invoked on each of the packages

```py
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
            "id": "id", # Reuse the ID from the external portals
            "notes": "notes", # This is the description
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
```

### Testing
This is only local testing and ensuring that the mapping is correct
and does not involve any actual imports to CUDC.
It calls the external API and gets all packages and maps them to CUDC catalogue entries.

Errors may occur in the actual import when the import is:
- missing the required fields
- `id`/`name` already exists
- `name` is too long
- etc..

```py
# Main entry for testing
if __name__ == "__main__":
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
    
```

### Import with custom organization mapping logic
> See [organization-mapping.py](./organization-mapping.py)

The property `owner_org` determines which organization the package belongs to.
In this example, the organization mapping logic is added to the end of `map_to_cudc_package` method.
The mapped organization should be already created in CUDC.

```py
from ckanext.udc_import_other_portals.logic import CKANBasedImport

class OrganizationMappingImport(CKANBasedImport):

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
        
        # Ogranization Mapping Logic
        # The mapped organization should be already created
        if src["organization"]["name"] == "city-of-toronto":
            target["owner_org"] = "city-of-toronto"
        elif src["organization"]["name"] == "city-of-mississauga":
            target["owner_org"] = "city-of-mississauga"
            
        if src["owner_division"] == "Transportation Services":
            target["owner_org"] = "city-of-toronto-transportation-services"
        # Add more organization mappings here
        # ...
        
        return target

# Define which class should be used for import, CUDC will use it as an entrypoint
DefaultImportClass = OrganizationMappingImport
```

### Import with custom organization creation
> See [organization-mapping-and-creation.py](./organization-mapping-and-creation.py)

> When doing Python imports, please ensure the import statements are within the method.

This example includes the organization creation logic in the `map_to_cudc_package` method.
It calls the `ensure_organization` method to create the organization if it does not exist in CUDC.


```py
from ckanext.udc_import_other_portals.logic import CKANBasedImport

class OrganizationMappingImport(CKANBasedImport):

    def map_to_cudc_package(self, src: dict, target: dict):
        """
        Map source package to cudc package.

        Args:
            src (dict): The source package that needs to be mapped.
            target (dict): The target package that imports into CUDC.
        """
        from ckanext.udc_import_other_portals.logic.base import (
            ensure_organization,
        )
                
        # Adding a prefix to the name to avoid potential collisions
        target["name"] = "city-toronto-" + src["name"]
        target["id"] = src["id"]
        target["title"] = src["title"]
        
        # Ogranization Mapping Logic
        if src["organization"]["name"] == "city-of-toronto":
            # This will ensure that the organization id exists in CUDC
            # If it does not exist, it will create it
            ensure_organization(self.build_context(), {
                "id": "city-of-toronto", # Should be unique, internal ID
                "name": "city-of-toronto", # Should be unique, used in URL
                "title": "City of Toronto",
                "description": "City of Toronto description",
            })
            target["owner_org"] = "city-of-toronto"
            
        if src["owner_division"] == "Transportation Services":
            target["owner_org"] = "city-of-toronto-transportation-services"
        # Add more organization mappings here
        # ...
        
        return target

# Define which class should be used for import, CUDC will use it as an entrypoint
DefaultImportClass = OrganizationMappingImport
```

### Import with defining organization mapping in the frontend
> See [organization-mapping-frontend.py](./organization-mapping-frontend.py)

In this example, the organization mapping is defined in the frontend:

Select `Import into its own organization, create if it does not exist, or map to an existing organization`
You will see a `Organization Mapping` button to define the mapping.

The import mode is set to `importToOwnOrg` and stored in `self.import_config.other_config.get("org_import_mode")`.
The organization mapping is passed to the backend as a `dict` in `self.import_config.other_config.get("org_mapping")`
and the handling of mapping and creating organizations is done before
calling the `map_to_cudc_package` method.

```py
from ckanext.udc_import_other_portals.logic import CKANBasedImport

class OrganizationMappingFrontendImport(CKANBasedImport):

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
        
        # Ogranization Mapping Logic
        # Nothing to do here, the organization mapping is done already before calling this method
        # target["owner_org"] is already set
        
        return target

# Define which class should be used for import, CUDC will use it as an entrypoint
DefaultImportClass = OrganizationMappingFrontendImport
```

### Import with custom license mapping and creation
> See [license-mapping-and-creation.py](./license-mapping-and-creation.py)

> When doing Python imports, please ensure the import statements are within the method.

This example includes the license creation logic in the `map_to_cudc_package` method.
It calls the `ensure_license` method to create the license if it does not exist in CUDC.

```py
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
```

### Import with custom tag mapping and creation
> See [tag-mapping-and-creation.py](./tag-mapping-and-creation.py)

> When doing Python imports, please ensure the import statements are within the method.

This example includes the tag creation logic in the `map_to_cudc_package` method.
Each of the tags should be provided as `{ "name": "tag-name" }` in the `tags` field.
`tag-name` is both ID and name of the tag. If the `tag-name` exists, it will be reused, otherwise, it will be created. 


```py
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
```

### Import with additional data from other API (Data Quality)
> See [access-other-api-data-quality.py](./access-other-api-data-quality.py)

> When doing Python imports, please ensure the import statements are within the method.

This example includes accessing additional data from another API and adding it to the package.

We override the `iterate_imports` method to include the quality of the package.

```py
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
```