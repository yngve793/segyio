import struct
import ebcdic
import sys


class Field:
    def __init__(self, name: str, d_type: str, endian: str = ">"):
        self.f_struct = struct.Struct(endian + d_type)
        self.name = name
        self.type = d_type
        self.value = None
        self.length = self.f_struct.size

    def __str__(self):
        return f"{self.name} ({self.length} bytes) - {self.type}"


fields = [
    ["I", "job_nr"],
    ["I", "line_nr"],
    ["I", "reel_nr"],
    ["H", "nr_of_traces"],
    ["H", "nr_of_aux"],
    ["H", "sample_int_1"],
    ["H", "sample_int_2"],
    ["H", "nr_samples_per_trace"],
    ["H", "nr_samples_per_data_trace"],
]


class BinaryFileHeader:
    @property
    def defined_fields(self):
        return [
            ["I", "job_nr"],
            ["I", "line_nr"],
            ["I", "reel_nr"],
            ["H", "nr_of_traces"],
            ["H", "nr_of_aux"],
            ["H", "sample_int_1"],
            ["H", "sample_int_2"],
            ["H", "nr_samples_per_trace"],
            ["H", "nr_samples_per_data_trace"],
            ["H", "format_code"],
            ["H", "ensemble_fold"],
            ["H", "trace_sorting_code"],
            ["H", "vertical_sum_code"],
            ["H", "sweep_freq_start"],
            ["H", "sweep_freq_end"],
            ["H", "sweep_freq_length"],
            ["H", "sweep_type_code"],
            ["H", "trace_nr"],
            ["H", "sweep_trace_taper_start"],
            ["H", "sweep_trace_taper_end"],
            ["H", "taper_type"],
            ["H", "correlated_trace"],
            ["H", "binary_gain_recovered"],
            ["H", "amp_recover_method"],
            ["H", "measurement_system"],
            ["H", "impulse_signal_polarity"],
            ["H", "vib_polarity_code"],
            ["I", "ext_nr_data_traces_pr_ensemble"],
            ["I", "ext_nr_aux_traces_pr_ensemble"],
            ["I", "ext_nr_sample_pr_data_trace"],
            ["Q", "ext_sample_interval_IEEE"],
            ["Q", "ext_sample_interval_original_IEEE"],
            ["I", "ext_sample_interval_original"],
            ["I", "ext_ensemble_fold"],
            ["I", "int_constant"],
            ["200s", "unassigned_1"],
            ["B", "major_ver"],
            ["B", "min_ver"],
            ["H", "trace_flag"],
            ["H", "nr_of_extensions"],
            ["H", "max_trace_headers"],
            ["H", "survey_type"],
            ["Q", "time_code"],
            ["Q", "ext_nr_of_traces"],
            ["I", "bytes_offset"],
            ["I", "nr_data_trailer"],
            ["66s", "unassigned_2"],
        ]

    BINARY_FILE_HEADER_SIZE = 400

    def __init__(self, data: bytes, offset: int = 3200):
        assert len(data) == BinaryFileHeader.BINARY_FILE_HEADER_SIZE
        self.offset = offset
        self.data = data
        self.pos = 0
        self.fields = []
        self.values = {}
        self.pos_value = {}
        for [f_d_type, f_name] in self.defined_fields:
            self.fields.append(Field(f_name, f_d_type))

        for field in self.fields:
            self.pos_value[field.name] = [
                self.offset + self.pos,
                self.offset + self.pos + field.length,
                field.type,
            ]
            self.values[field.name] = field.f_struct.unpack(
                data[self.pos : self.pos + field.length]
            )[0]
            self.pos += field.length

        assert self.pos == BinaryFileHeader.BINARY_FILE_HEADER_SIZE
        assert (
            self.values["int_constant"] == 16909060
        ), f"Wrong endianness {self.values["int_constant"]}"

    def dump_data(self):
        out_data = b""
        for field in self.fields:
            print(field, self.values[field.name])
            out_data += field.f_struct.pack(self.values[field.name])
        return out_data

    def print_values(self):
        for field in self.fields:
            print(
                f"[{self.pos_value[field.name].__str__().ljust(17)}]  "
                + f"{field.name.ljust(35)} : {self.values[field.name]}"
            )


class TextualFileHeader:
    TEXTUAL_FILE_HEADER_SIZE = 3200

    def __init__(self, data: bytes):
        assert len(data) == TextualFileHeader.TEXTUAL_FILE_HEADER_SIZE
        self.data = data
        self.text = data.decode("cp1141")

        self.lines = []
        for i in range(int(TextualFileHeader.TEXTUAL_FILE_HEADER_SIZE / 80)):
            self.lines.append(self.text[i * 80 : (i + 1) * 80])

    def print_lines(self):
        for line in self.lines:
            print(line)


def read_file_from_disk(_file_name):
    with open(_file_name, "rb") as f:
        data = f.read()

    pos = 0
    textual_file_header = data[pos : pos + TextualFileHeader.TEXTUAL_FILE_HEADER_SIZE]
    pos += TextualFileHeader.TEXTUAL_FILE_HEADER_SIZE

    binary_file_header = data[pos : pos + BinaryFileHeader.BINARY_FILE_HEADER_SIZE]
    pos += BinaryFileHeader.BINARY_FILE_HEADER_SIZE

    rest = data[pos:]

    return [textual_file_header, binary_file_header, rest]


def write_file_to_disk(write_file_name, textual_file_header, bfh, rest):
    print("Write file:" + write_file_name)
    with open(write_file_name, "wb") as f:
        f.write(textual_file_header)
        f.write(bfh.dump_data())
        f.write(rest)


def main():
    file_name = sys.argv[1:][0]
    [textual_file_header, binary_file_header, rest] = read_file_from_disk(file_name)

    tfh = TextualFileHeader(textual_file_header)
    tfh.print_lines()

    bfh = BinaryFileHeader(binary_file_header)
    bfh.print_values()

    # Set desired values in the binary file header
    bfh.values["nr_of_extensions"] = 16

    if len(sys.argv) > 2:
        write_file_name = sys.argv[2]
        write_file_to_disk(write_file_name, textual_file_header, bfh, rest)


if __name__ == "__main__":
    main()
