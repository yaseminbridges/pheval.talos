import json
import re
from pathlib import Path

from phenopackets import Cohort, Family, Individual, MetaData, Phenopacket, Resource, Sex
from pheval.utils.file_utils import all_files
from pheval.utils.phenopacket_utils import phenopacket_reader, write_phenopacket

reported_sex_map = {1: Sex.MALE, 2: Sex.FEMALE}
sex_map_conversion = {1: "2", 2: "1"}


def sanitise_id(s: str) -> str:
    """Make IDs safe for VCF/Hail: no spaces or slashes, only [A-Za-z0-9_.-]."""
    s = s.replace("/", "_").replace(" ", "_")
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)

def extract_phenopacket(phenopacket: Family | Phenopacket, is_family: bool) -> Phenopacket:
    """
    Extract phenotypic and subject information from a given phenopacket.
    Args:
    phenopacket : Phenopacket
        The phenopacket containing subject and phenotypic information.
    Returns:
    Phenopacket
        A new instance of Phenopacket containing extracted subject and phenotypic
        details.
    """
    if is_family:
        return Phenopacket(
            id=sanitise_id(phenopacket.proband.subject.id),
            subject=Individual(
                id=sanitise_id(phenopacket.id) + "_FAM",
                sex=reported_sex_map.get(phenopacket.proband.subject.sex, Sex.UNKNOWN_SEX),
            ),
            phenotypic_features=list(phenopacket.proband.phenotypic_features),
        )

    return Phenopacket(
        id=sanitise_id(phenopacket.subject.id),
        subject=Individual(
            id=sanitise_id(phenopacket.id) + "_FAM",
            sex=reported_sex_map.get(phenopacket.subject.sex, Sex.UNKNOWN_SEX),
        ),
        phenotypic_features=list(phenopacket.phenotypic_features),
    )


def create_pedigree_for_phenopacket(phenopacket: Phenopacket | Family, pedigree: list[str], is_family: bool) -> list[str]:
    """
    Generate a pedigree file content for a given Phenopacket or Family instance.
    Args:
        phenopacket (Phenopacket | Family): A Phenopacket or Family instance containing
        subject or pedigree data.
        pedigree (list[str]): List of strings representing pedigree entries. This list
        is modified in-place by appending new entries.
    Returns:
        list[str]: The updated pedigree list containing pedigree data in correctly
        formatted strings.
    """
    if is_family:
        phenopacket_ped = phenopacket.pedigree
        for person in phenopacket_ped.persons:
            pedigree.append(
                f"{sanitise_id(person.family_id)}\t{sanitise_id(person.individual_id)}\t"
                f"{sanitise_id(person.paternal_id)}\t{sanitise_id(person.maternal_id)}\t"
                f"{sex_map_conversion.get(phenopacket.subject.sex, 0)}\t{person.affected_status}\n"
            )
        return pedigree
    pedigree.append(
        f"{sanitise_id(phenopacket.subject.id)}_FAM\t{sanitise_id(phenopacket.subject.id)}\t"
        f"0\t0\t"
        f"{sex_map_conversion.get(phenopacket.subject.sex, 0)}\t2\n"
    )
    return pedigree


def create_cohort(testdata_dir: Path) -> None:
    """
    Creates a cohort by processing a phenopacket directory.
    Args:
        testdata_dir (Path): Path to the directory containing the phenopacket directory.
    """
    phenopacket_dir = testdata_dir.joinpath("phenopackets")
    cohort = Cohort(
        id=testdata_dir.name,
        description=f"Phenotypic data from {testdata_dir.name}",
        members=[],
        meta_data=MetaData(
            created_by="TalosPhEvalRunner",
            resources=[
                Resource(
                    id="hp",
                    name="Human Phenotype Ontology",
                    url="http://www.human-phenotype-ontology.org",
                    version="2024-08-13",
                    namespace_prefix="HP",
                    iri_prefix="http://purl.obolibrary.org/obo/HP_",
                ),
            ],
        ),
    )
    pedigree = []
    for phenopacket_path in all_files(phenopacket_dir):
        is_family = "proband" in json.load(open(phenopacket_path))
        phenopacket = phenopacket_reader(phenopacket_path)
        cohort.members.append(
            extract_phenopacket(phenopacket, is_family),
        )
        pedigree = create_pedigree_for_phenopacket(phenopacket, pedigree, is_family)
    with open(testdata_dir.joinpath("pedigree.ped"), "w") as f:
        f.writelines(pedigree)
    write_phenopacket(cohort, testdata_dir.joinpath(f"{testdata_dir.name}_cohort.json"))
