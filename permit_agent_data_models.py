from pydantic import BaseModel, Field
from typing import Optional, Literal


class Address(BaseModel):
    street_num: int
    street: str
    suite: Optional[str]
    city: str
    state: str
    zip: str


class Contact(BaseModel):
    name: str
    phone: str
    email: str
    mailing_address: Optional[Address]
    # TODO validator for email and phone


class Contractor(BaseModel):
    business_name: str
    license_num: str
    business_address: Address
    contact: Contact


class PermitInfo(BaseModel):
    project_address: Address = Field(
        description="Address of the proposed solar project."
    )
    # jusrisdiction: str
    project_owner: Contact = Field(description="Owner of the proposed solar project.")
    building_type: Literal[
        "single family",
        "duplex",
        "multi-family",
        "commercial/industrial",
        "new construction",
        "other",
    ] = Field(
        description="Building type of proposed solar installation. One of: single family, duplex, multi family, commercial/industrial, new construction, or other."
    )
    new_or_existing: Literal["new", "additional", "replacement"] = Field(
        description="Is the proposed solar installation new, additional capacity or a replacement."
    )
    system_type: Literal["roof mount", "ground mount", "building integrated/other"] = (
        Field(
            description="Proposed solar installation system type. One of: roof mount, ground mount, building integrated, or other."
        )
    )
    inverter_config: Literal[
        "string inverter",
        "string inverter w/ DC Converters",
        "microinverters or AC modules",
    ] = Field(
        description="Proposed solar installation inverter configuration. One of: string inverter, string inverter w/ DC Converters, microinverters or AC modules"
    )
    system_size: float = Field(description="Total PV system size in kW DC")
    area: float = Field(description="Total square footage of PV system")
    valuation: float = Field(description="Project valuation ($)")
    project_description: str = Field(
        description=("Brief description of proposed solar project.")
    )
    contractor: Contractor = Field(
        description="Main contractor of proposed solar project."
    )
    electrical_subcontractor: Optional[Contractor] = Field(
        description="Electrical subcontractor of proposed solar project."
    )


# class with subset of fields used in development
class PermitInfoTruncatedForTest(BaseModel):
    project_address: Address = Field(
        description="Address of the proposed solar project."
    )
    building_type: Literal[
        "single family",
        "duplex",
        "multi-family",
        "commercial/industrial",
        "new construction",
        "other",
    ] = Field(
        description="Building type of proposed solar installation. One of: single family, duplex, multi family, commercial/industrial, new construction, or other."
    )
    new_or_existing: Literal["new", "additional", "replacement"] = Field(
        description="Is the proposed solar installation new, additional capacity or a replacement."
    )
