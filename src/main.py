import matplotlib.pyplot as plt
import sys
import time
import json
from src.extractor import get_pdf_query_partial_file, pipeline_pdf_query_to_json_item
from src.models.Plant import Plant
#log_file = open("procesamiento_log.txt", "w")
#sys.stdout = log_file

start_time = time.time()

no_success = 0
no_failure = 0
failures = []
plants = []

full_range = range(27, 228, 2)
sample_range = range(27, 50, 2)
for i in full_range:
    real_start_page, real_end_page = i, i + 1
    print(f"Currently processing pages: {real_start_page} and {real_end_page}")

    delta_x = 1
    virtual_page_start, virtual_page_end = real_start_page - delta_x, real_end_page - delta_x

    pdf_query = get_pdf_query_partial_file(pages_range=range(virtual_page_start, virtual_page_end + 1))
    plant_info: Plant = pipeline_pdf_query_to_json_item(file=pdf_query,
                                                        name_xml=f"plants_{real_start_page}_{real_end_page}.xml",
                                                        source_pages=[real_start_page, real_end_page], export_xml=True)

    plants.append(plant_info.model_dump())
    print(f"Progress: {i}/228")

with open('./src/output/jsons/collections/plants.json', 'w', encoding='utf-8') as json_file:
    json.dump(plants, json_file, ensure_ascii=False, indent=4)

print("El archivo JSON ha sido guardado exitosamente.")
end_time = time.time()
elapsed_time = end_time - start_time
