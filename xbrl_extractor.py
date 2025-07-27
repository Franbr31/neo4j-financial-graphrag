from lxml import etree
import requests

def extract_xbrl_metric(xbrl_url: str, metric_tag: str, ns_url: str = "http://fasb.org/us-gaap/2023-01-31"):
    """
    Extracts a financial metric from an XBRL instance document.

    :param xbrl_url: URL to the XBRL instance .xml file
    :param metric_tag: Tag of the metric (e.g. "us-gaap:NetIncomeLoss")
    :param ns_url: Namespace URL for the XBRL taxonomy
    :return: dict with value, period, unit, and contextRef
    """
    try:
        response = requests.get(xbrl_url)
        tree = etree.fromstring(response.content)
    except Exception as e:
        return {"error": f"Failed to load or parse XML: {str(e)}"}

    ns = {"us-gaap": ns_url}

    metric_elem = tree.find(f".//{metric_tag}", namespaces=ns)
    if metric_elem is None:
        return {"error": f"Metric {metric_tag} not found"}

    value = metric_elem.text
    context_ref = metric_elem.attrib.get("contextRef")
    unit_ref = metric_elem.attrib.get("unitRef")

    # Extract period
    context_elem = tree.find(f".//context[@id='{context_ref}']")
    if context_elem is not None:
        start = context_elem.findtext(".//startDate")
        end = context_elem.findtext(".//endDate")
    else:
        start, end = None, None

    # Extract unit
    unit_elem = tree.find(f".//unit[@id='{unit_ref}']")
    unit = unit_elem.findtext(".//measure") if unit_elem is not None else "unknown"

    return {
        "metric": metric_tag,
        "value": value,
        "unit": unit,
        "contextRef": context_ref,
        "period": {"start": start, "end": end}
    }