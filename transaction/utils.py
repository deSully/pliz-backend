EXTERNAL_REFERENCE_EXTRACTORS = {
    "djamo": lambda response: response.get("id"),
    "wave": lambda response: response.get("body", {}).get("id"),
    "orange_money": lambda response: response.get("body", {}).get("id"),
}


def get_external_reference(partner: str, response: dict):
    extractor = EXTERNAL_REFERENCE_EXTRACTORS.get(partner.lower())
    if not extractor:
        raise ValueError(f"Unsupported partner: {partner}")
    return extractor(response)
