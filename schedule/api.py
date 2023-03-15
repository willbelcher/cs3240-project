import requests

base_url = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01"
field_pattern = "&{}={}"

def get_course_list(year=2023, term="Fall", dept=False, instructor=False):
    if year == "": year = 2023
    
    num_term = 0
    if term == "Fall":
        num_term = 8
    elif term == "Spring":
        num_term = 2

    search_url = base_url
    search_url += field_pattern.format("term", "1{}{}".format(int(year)%100, num_term))

    if dept:
        search_url += field_pattern.format("subject", dept)
    if instructor:
        search_url += field_pattern.format("instructor_name", instructor)
    
    resp = requests.get(search_url)
    courses = resp.json()

    return courses
