# type: ignore
import os
import shutil
import tempfile

import networkx as nx

from geniusrise_healthcare.io import (
    save_concept_dict,
    save_networkx_graph,
    save_faiss_index,
)
from geniusrise_healthcare.snomed import load_snomed_into_networkx, unzip_snomed_ct

from transformers import AutoTokenizer, AutoModel
import torch
import faiss


def test_unzip_snomed_ct():
    # Create a temporary directory to hold the zip and extracted files
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = "./data/SnomedCT_InternationalRF2_PRODUCTION_20230901T120000Z.zip"
        extract_path = "./data/snomed"

        shutil.rmtree(extract_path, ignore_errors=True)

        # Run the unzip_snomed_ct function
        unzip_snomed_ct(zip_path, extract_path)

        # Check if the files were correctly extracted
        assert os.path.exists(os.path.join(extract_path, "SnomedCT_InternationalRF2_PRODUCTION_20230901T120000Z"))
        assert os.path.exists(
            os.path.join(
                extract_path,
                "SnomedCT_InternationalRF2_PRODUCTION_20230901T120000Z/release_package_information.json",
            )
        )


def test_load_snomed_into_networkx_no_index():
    # Create a temporary directory to hold the SNOMED-CT files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy the SNOMED-CT snapshot files to the temporary directory
        snomed_files = [
            "sct2_Concept_Snapshot_INT_20230901.txt",
            "sct2_Description_Snapshot-en_INT_20230901.txt",
            "sct2_Identifier_Snapshot_INT_20230901.txt",
            "sct2_RelationshipConcreteValues_Snapshot_INT_20230901.txt",
            "sct2_Relationship_Snapshot_INT_20230901.txt",
            "sct2_sRefset_OWLExpressionSnapshot_INT_20230901.txt",
            "sct2_StatedRelationship_Snapshot_INT_20230901.txt",
            "sct2_TextDefinition_Snapshot-en_INT_20230901.txt",
        ]
        for file in snomed_files:
            shutil.copy(
                os.path.join(
                    "./data/snomed/SnomedCT_InternationalRF2_PRODUCTION_20230901T120000Z/Snapshot/Terminology",
                    file,
                ),
                os.path.join(tmpdir, file),
            )

        # Run the function
        G, description_id_to_concept, concept_id_to_concept, concept_id_to_text_definition = load_snomed_into_networkx(
            tmpdir, batch_size=100000, skip_embedding=True
        )

        # Save the data
        save_networkx_graph(G, "./saved/snomed.graph")
        save_concept_dict(description_id_to_concept, "./saved/description_id_to_concept.pickle")
        save_concept_dict(concept_id_to_concept, "./saved/concept_id_to_concept.pickle")
        save_concept_dict(concept_id_to_text_definition, "./saved/concept_id_to_text_definition.pickle")

        # Validate the output
        assert isinstance(G, nx.DiGraph)
        assert G.number_of_nodes() > 100000
        assert G.number_of_edges() > 100000


def test_load_snomed_into_networkx():
    return True

    # Create a temporary directory to hold the SNOMED-CT files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy the SNOMED-CT snapshot files to the temporary directory
        snomed_files = [
            "sct2_Description_Snapshot-en_INT_20230901.txt",
            "sct2_Relationship_Snapshot_INT_20230901.txt",
        ]
        for file in snomed_files:
            shutil.copy(
                os.path.join(
                    "./data/snomed/SnomedCT_InternationalRF2_PRODUCTION_20230901T120000Z/Snapshot/Terminology", file
                ),
                os.path.join(tmpdir, file),
            )

        # Initialize tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        model = AutoModel.from_pretrained("bert-base-uncased")

        # Initialize FAISS index
        quantizer = faiss.IndexFlatL2(768)  # 768 is the dimension of BERT embeddings
        faiss_index = faiss.IndexIDMap(quantizer)

        # Run the function
        G, description_id_to_concept, concept_id_to_concept = load_snomed_into_networkx(
            tmpdir, tokenizer, model, faiss_index, batch_size=100000
        )

        # Save the data
        shutil.rmtree("./saved", ignore_errors=True)
        os.mkdir("./saved")
        save_networkx_graph(G, "./saved/snomed.graph")
        save_faiss_index(faiss_index, "./saved/faiss.index")
        save_concept_dict(description_id_to_concept, "./saved/description_id_to_concept.pickle")
        save_concept_dict(concept_id_to_concept, "./saved/concept_id_to_concept.pickle")

        # Validate the output
        assert isinstance(G, nx.DiGraph)
        assert G.number_of_nodes() > 1680336
        assert G.number_of_edges() > 1191042

        assert isinstance(description_id_to_concept, dict)
        assert len(description_id_to_concept) > 1317012

        assert faiss_index.ntotal > 1317012


def test_load_snomed_into_networkx_llama_local():
    return True

    # Initialize tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(
        "/run/media/ixaxaar/hynix_2tb/models/Llama-2-7b-hf", torch_dtype=torch.float16, model_max_length=512
    )
    model = AutoModel.from_pretrained("/run/media/ixaxaar/hynix_2tb/models/Llama-2-7b-hf", torch_dtype=torch.float16)

    # Initialize FAISS index
    quantizer = faiss.IndexFlatL2(4096)  # 768 is the dimension of BERT embeddings
    faiss_index = faiss.IndexIDMap(quantizer)

    # Run the function
    G, description_id_to_concept, concept_id_to_concept, concept_id_to_text_definition = load_snomed_into_networkx(
        "data/snomed/SnomedCT_InternationalRF2_PRODUCTION_20230901T120000Z/Snapshot/Terminology",
        batch_size=100000,
        skip_embedding=False,
        model=model,
        tokenizer=tokenizer,
        faiss_index=faiss_index,
    )

    # Validate the output
    assert isinstance(G, nx.DiGraph)
    assert G.number_of_nodes() > 100000
    assert G.number_of_edges() > 100000

    # Save the data
    save_networkx_graph(G, "./saved-llama-7b/snomed.graph")
    save_faiss_index(faiss_index, "./saved-llama-7b/faiss.index")
    save_concept_dict(description_id_to_concept, "./saved-llama-7b/description_id_to_concept.pickle")
    save_concept_dict(concept_id_to_concept, "./saved-llama-7b/concept_id_to_concept.pickle")
    save_concept_dict(concept_id_to_text_definition, "./saved-llama-7b/concept_id_to_text_definition.pickle")
