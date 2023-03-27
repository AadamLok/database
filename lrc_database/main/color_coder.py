COLOR_CODE = {
	"SI": "orange",
	"Tutoring": "green",
	"Group Tutoring": "coral",
	"Training": "red",
	"Observation": "blue",
	"Class": "magenta",
	"Preparation": "teal",
	"Meeting": "olive",
	"OURS Mentor": "brown",
	"Other": "black"
}

def color_coder(shift_kind):
	if shift_kind not in COLOR_CODE:
		return "black"
	return COLOR_CODE[shift_kind]

def get_color_coder_dict():
	return COLOR_CODE