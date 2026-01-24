import csv
import os
from lxml import etree

# Constants
XML_PATH = "data/SDN_ADVANCED.XML"
PARTIES_CSV = "data/parties.csv"
RELATIONSHIPS_CSV = "data/relationships.csv"

# Namespaces
NS = {"ns": "http://www.un.org/sanctions/1.0"}

def get_text(element, xpath, namespaces=None):
    res = element.xpath(xpath, namespaces=namespaces)
    return res[0].text if res else ""

def flatten_xml():
    print(f"Starting to parse {XML_PATH}...")
    
    # Check if files exist
    if not os.path.exists(XML_PATH):
        print(f"Error: {XML_PATH} not found.")
        return

    # Open CSV files
    with open(PARTIES_CSV, 'w', newline='', encoding='utf-8') as p_file, \
         open(RELATIONSHIPS_CSV, 'w', newline='', encoding='utf-8') as r_file:
        
        party_writer = csv.writer(p_file)
        rel_writer = csv.writer(r_file)
        
        # Headers
        party_writer.writerow(["party_id", "primary_name", "party_type"])
        rel_writer.writerow(["rel_id", "from_party", "to_party", "rel_type"])
        
        # Iterative parsing for memory efficiency
        context = etree.iterparse(XML_PATH, events=('end',), tag='{*}DistinctParty')
        
        count = 0
        for event, elem in context:
            party_id = elem.get("FixedRef")
            
            # Primary Name
            primary_name = ""
            name_elem = elem.find(".//{*}Identity[@Primary='true']//{*}NamePartValue")
            if name_elem is not None:
                primary_name = name_elem.text

            # Type and SubType
            sub_type_elem = elem.find(".//{*}Profile")
            if sub_type_elem is not None:
                party_subtype_id = sub_type_elem.get("PartySubTypeID")
                party_writer.writerow([party_id, primary_name, party_subtype_id])
            else:
                party_writer.writerow([party_id, primary_name, ""])
            
            count += 1
            if count % 1000 == 0:
                print(f"Processed {count} parties...")
            
            # Clear element to save memory
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
        
        print(f"Total parties processed: {count}")
        
        # Relationships are usually in a separate section in this XML schema
        # Let's reset the context for ProfileRelationships
        del context
        context = etree.iterparse(XML_PATH, events=('end',), tag='{*}ProfileRelationship')
        
        rel_count = 0
        for event, elem in context:
            rel_id = elem.get("ID")
            from_p = elem.get("From-ProfileID")
            to_p = elem.get("To-ProfileID")
            rel_type = elem.get("RelationTypeID")
            
            rel_writer.writerow([rel_id, from_p, to_p, rel_type])
            
            rel_count += 1
            if rel_count % 1000 == 0:
                print(f"Processed {rel_count} relationships...")
                
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
                
        print(f"Total relationships processed: {rel_count}")

if __name__ == "__main__":
    flatten_xml()
