from pdfquery import  PDFQuery
import os
import pickle
import logging
from src.models.Plant import Plant
from lxml.etree import XMLParser
from typing import List, Optional
import re

logger = logging.getLogger(__name__)

#INPUTS
PATH_TO_PICKLES = os.path.join("src", "input", "pickles")
PATH_TO_PDFS =  os.path.join("src", "input", "pdfs")


#OUTPUTS
PATH_TO_XML = os.path.join("src", "output", "xmls")
PATH_TO_COLLECTIONS = os.path.join("src", "output", "jsons", "collections")
PATH_TO_JSONS_ITEMS = os.path.join("src", "output", "jsons", "items")

# Auxiliar functions

def get_pdf_query_complete_file(file_name: str = "Vademecum_plantas_medicinales_Guatemala", freeze=True) -> PDFQuery | None:
    pickle_path = os.path.join(PATH_TO_PICKLES, f"{file_name}.pkl")

    if os.path.exists(pickle_path):
        with open(pickle_path, 'rb') as file:
            pdf_query = pickle.load(file)
        logger.info(f"Pickle file restored for {file_name}")
        return pdf_query

    logger.warning(f"Couldn't find pickle file named {file_name}")
    logger.info(f"Starting process to restore from pdf file")

    pdf_path = os.path.join(PATH_TO_PDFS, f"{file_name}.pdf")

    if not os.path.exists(pdf_path):
        logger.error(f"Couldn't find neither pickle nor PDF file named {file_name}")
        return None

    logger.info(f"Starting process to restore from PDF file")
    pdf_query = PDFQuery(pdf_path)
    pdf_query.load()

    if freeze:
        with open(pickle_path, 'wb') as file:
            pickle.dump(pdf_query, file)
        logger.info(f"PDFQuery object saved as pickle for {file_name}")

    return pdf_query

def get_pdf_query_partial_file(file_name: str = "Vademecum_plantas_medicinales_Guatemala", pages_range: range = None):
    pdf_path = os.path.join(PATH_TO_PDFS, f"{file_name}.pdf")
    if not os.path.exists(pdf_path):
        logger.error(f"Couldn't find neither pickle nor PDF file named {file_name}")
        return None
    logger.info(f"Starting process to restore from PDF file")
    pdf_query = PDFQuery(pdf_path)
    if pages_range is None:
        pdf_query.load()
    else:
        pdf_query.load(*pages_range)
    return pdf_query


# Data engineering

def pipeline_pdf_query_to_json_item(file: PDFQuery, name_xml, source_pages, export_xml = False) -> Plant:
    file_tree = file.tree

    if export_xml:
        xml_filepath = os.path.join(PATH_TO_XML, f"{name_xml}.xml")
        file.tree.write(xml_filepath, pretty_print=True)

    title = task_extract_title(file_tree)
    synonyms = task_extract_synonyms(file_tree, plant_name=title)
    other_names = task_extract_other_names(file_tree, plant_name=title)
    other_names = [item for item in other_names if item!=""]
    medical_used_parts = task_extract_medical_used_parts(file_tree, plant_name=title)

    habitat = task_extract_habitat(file_tree, ["OBTENCIÓN"])

    return Plant(
        name=title,
        source_pages=source_pages,
        synonyms=synonyms,
        other_popular_names=other_names,
        medical_used_parts=medical_used_parts,
        description="<description>",
        habitat=habitat,
        obtaining="<obtaining>",
        medicinal_uses_and_properties="<medicinal_uses>",
        experimental_and_clinical_pharmacology="<pharmacology>"

    )

def task_extract_title(file_tree: XMLParser):
    lt_page_element = file_tree.xpath('//LTPage[@pageid="1"]')

    if lt_page_element:
        element = lt_page_element[0].xpath('.//LTTextBoxHorizontal[@index="1"]')

        if element and len(element) > 0:
            title_element = element[0]
            found_title_text: str = ''.join(title_element.itertext()).strip()

            if found_title_text.upper() != "SINONIMIAS":
                print(found_title_text)
                return found_title_text
            else:
                # Special case
                """
                In XML export. Name got lost into to tags
                    <LTTextLineHorizontal y0="688.056" y1="712.056" x0="431.623" x1="463.332" width="31.709" height="24.0" bbox="[431.623, 688.056, 463.332, 712.056]" word_margin="0.1"><LTTextBoxHorizontal y0="688.056" y1="712.056" x0="431.623" x1="463.332" width="31.709" height="24.0" bbox="[431.623, 688.056, 463.332, 712.056]" index="3">JO </LTTextBoxHorizontal></LTTextLineHorizontal>
                    <LTTextLineVertical y0="688.056" y1="725.756" x0="417.42" x1="432.499" width="15.079" height="37.7" bbox="[417.42, 688.056, 432.499, 725.756]" word_margin="0.1"><LTTextBoxVertical y0="688.056" y1="725.756" x0="417.42" x1="432.499" width="15.079" height="37.7" bbox="[417.42, 688.056, 432.499, 725.756]" index="4"> A </LTTextBoxVertical></LTTextLineVertical>

                Texts should be joined. Since this happens only at this specific item. Hard coding the title is practical. 
                """
                # Hardcode para el caso específico
                return "AJO"
    return None

def task_extract_synonyms(file_tree: XMLParser, plant_name: str):
    if plant_name == "AJO":
        # Skip por simplicity. It doesn't contains synonyms anyways.
        return []

    lt_page_element = file_tree.xpath('//LTPage[@pageid="1"]')
    if not lt_page_element:
        return []

    collected_texts = []
    is_text_after_dibujo_text = False

    for element in lt_page_element[0].iter():
        if element.text:
            text_content: str = element.text.strip()

            if text_content.upper().startswith("OTROS NOMBRE") or text_content.upper().startswith("NOMBRE POPULARES")  :
                return collected_texts

            if is_text_after_dibujo_text and text_content!="SINONIMIAS" and text_content!="y Pöll en Cáceres et al. 1990.":
                collected_texts.append(text_content)

            if not is_text_after_dibujo_text:
                is_text_after_dibujo_text = text_content.lower().startswith("dibujo") # Founds dibujo text

    return collected_texts

def task_extract_other_names(file_tree: XMLParser, plant_name: str):
    if plant_name == "AJO":
        # Skip por simplicity. It doesn't contains synonyms anyways.
        return []
    lt_page_element = file_tree.xpath('//LTPage[@pageid="1"]')
    next_section_titles = [
        "PARTES USADAS MEDICINALMENTE",
        "PARTE USADA MEDICINALMENTE",
        "PARTES USADAS MEDICINALMEMNTE",
        "PARTES USADAS MEDICINALM",
        "PARTES USADAS MEDICIALMENTE"

    ]
    if not lt_page_element:
        return []

    collected_other_names = []
    found_starting_point = False
    for element in lt_page_element[0].iter():

        if not found_starting_point:
            if element.text:
                text_content: str = element.text.strip()
                found_starting_point = text_content.upper().startswith("OTROS NOMBRES") or text_content.upper().startswith("NOMBRE POPULARES")

        else:
            if element.text:
                text_content: str = element.text.strip()
                if text_content in next_section_titles:
                    return collected_other_names

                split_text_contents = text_content.split(",")
                split_text_contents = [item.strip() for item in split_text_contents]
                collected_other_names.extend(split_text_contents)

    return collected_other_names

def task_extract_medical_used_parts(file_tree: XMLParser, plant_name: str):
    lt_page_element = file_tree.xpath('//LTPage[@pageid="1"]')

    if not lt_page_element:
        return []

    collected_medical_parts = []
    found_starting_point = False
    for element in lt_page_element[0].iter():

        if not found_starting_point:
            if element.text:
                text_content: str = element.text.strip()
                found_starting_point = text_content.upper().startswith("PARTES USADAS")

        else:
            if element.text:
                text_content: str = element.text.strip()
                if text_content == "ENTE":
                    continue
                collected_medical_parts.append(text_content)
                # assumes there's only one tag containing medical used parts
                return collected_medical_parts

    return collected_medical_parts

def task_extract_habitat(file_tree: XMLParser, next_titles: List[str]) -> Optional[str]:
    """
    Apply to habitat and Obtencion only

    :param file_tree:
    :param next_titles:
    :return:
    """
    section_title = "HÁBITAT"

    lt_page_element = file_tree.xpath('//LTPage[@pageid="1"]')

    if not lt_page_element:
        return None

    found_starting_point = False
    collected_texts = []

    for element in lt_page_element[0].iter():
        if element.text:
            text_content: str = element.text.strip()

            if not found_starting_point:
                if text_content.upper().startswith(section_title.upper()):
                    found_starting_point = True
            else:
                if any(text_content.upper().startswith(title.upper()) for title in next_titles):
                    break
                collected_texts.append(text_content)


    if not collected_texts:
        return None

    text =  " ".join(collected_texts)

    cleaned_text = re.sub(r'\b\d+\.', '', text)

    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    cleaned_text = re.sub(r'- ', '', cleaned_text).strip()

    return cleaned_text


