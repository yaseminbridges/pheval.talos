import subprocess
from pathlib import Path


def run_annotation(input_dir: Path) -> None:
    """
    Run the annotation process using Nextflow.
    Args:
        input_dir (Path): The directory containing the necessary Nextflow workflow and
        configuration files for the annotation process.
    Returns:
        None
    """
    subprocess.run(
        ["nextflow", "-c", f"{input_dir}/nextflow/annotation.config", "run", f"{input_dir}/nextflow/annotation.nf", "-resume"],
        check=False,
        shell=False,
    )


def run_talos(input_dir: Path, testdata_dir: Path, raw_results_dir: Path) -> None:
    """
    Run the Talos Nextflow pipeline.
    Args:
        input_dir (Path): The directory containing the Talos Nextflow configuration and pipeline script.
        testdata_dir (Path): The directory containing the phenopackets file for the cohort data.
        raw_results_dir (Path): The raw results directory.
    Returns:
        None
    """
    subprocess.run(
        [
            "nextflow",
            "-c",
            f"{input_dir}/nextflow/talos.config",
            "run",
            f"{input_dir}/nextflow/talos.nf",
            f"--matrix_table",
            f"{raw_results_dir}/{testdata_dir.name}.mt",
            "--phenopackets",
            testdata_dir.joinpath(f"{testdata_dir.name}_cohort.json"),
            "-resume",
        ],
        check=False,
    )
