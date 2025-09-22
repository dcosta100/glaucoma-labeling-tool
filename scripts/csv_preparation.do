use "C:\Users\dxr1276\Box\PROJECTS\VF_GRADINGS\opv_export_masked_20220901.dta", clear


* Generate age
gen age = (aeexamdate_shift - aedob_shift)/365.25

* Keep only 24-2:
keep if testpattern == "24-2"

* Counters:
sort maskedid eye aeexamdate_shift
by maskedid eye: gen visual_field_count = _N
by maskedid eye: gen visual_field_number = _n

keep maskedid eye age aedob_shift aeexamdate_shift pdf_filename opv_filename visual_field_count visual_field_number

export delimited "C:\Users\dxr1276\OneDrive\Projects\glaucoma-labeling-tool\data\opv_24-2_prepared.csv", replace