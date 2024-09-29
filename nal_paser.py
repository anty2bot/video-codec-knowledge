#!/usr/bin/env python3
"""
Author: Dot(anty2bot@gmail.com)
Date: 2024-09-29
Description: This script performs video nal parse
References:
  [1] - [ITU-T H.264 (V14) (08/2021)](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-H.264-202108-S!!PDF-E&type=items)

License: MIT License
"""

from bitstring import BitStream


class Util:

    def __init__(self, data: bytearray) -> None:
        self.__bitstream = BitStream(data)
        pass

    def ue(self):
        """Reads unsigned Exp-Golomb code (ue(v)) from the bitstream."""
        assert isinstance(self.__bitstream, BitStream)

        leading_zero_bits = 0
        while self.__bitstream.read("bool") == 0:
            leading_zero_bits += 1

        if leading_zero_bits == 0:
            return 0

        remaining_bits = self.__bitstream.read(f"uint:{leading_zero_bits}")
        assert isinstance(remaining_bits, int)

        return (1 << leading_zero_bits) - 1 + remaining_bits

    def u(self, size):
        assert isinstance(self.__bitstream, BitStream)
        return self.__bitstream.read(f"uint:{size}")


def enum_nals(data: bytes):
    # Define NAL unit start codes (long and short forms)
    start_code_prefixes = [b"\x00\x00\x00\x01", b"\x00\x00\x01"]

    nal_units_index_array = []
    pos = 0

    while pos < len(data):
        # Find the next occurrence of either start code prefix
        next_prefix_pos = -1
        next_prefix_len = 0

        for prefix in start_code_prefixes:
            prefix_pos = data.find(prefix, pos)

            if prefix_pos != -1 and (
                next_prefix_pos == -1 or prefix_pos < next_prefix_pos
            ):
                next_prefix_pos = prefix_pos
                next_prefix_len = len(prefix)

        # If no more prefixes are found, break the loop
        if next_prefix_pos == -1:
            break

        # Move the position to the end of the current start code prefix
        nal_start_pos = next_prefix_pos + next_prefix_len
        nal_units_index_array.append(nal_start_pos)

        # Move to the next position for searching
        pos = nal_start_pos

    return nal_units_index_array


def seq_parameter_set_data_description():
    """
    As described in Section 7.3.2.1.1 | Sequence parameter set data syntax

    [+]--[00]seq_parameter_set_data() {{
     |    |
     |    |--- profile_idc                                                                u(8) {{ profile_idc }}
     |    |--- constraint_set0_flag                                                       u(1)
     |    |--- constraint_set1_flag                                                       u(1)
     |    |--- constraint_set2_flag                                                       u(1)
     |    |--- constraint_set3_flag                                                       u(1)
     |    |--- constraint_set4_flag                                                       u(1)
     |    |--- constraint_set5_flag                                                       u(1)
     |    |--- reserved_zero_2bits                                                        u(2)
     |    |--- level_idc                                                                  u(8)
     |    |--- seq_parameter_set_id                                                       ue(v)
     |    |
     |   [-]-- if (profile_idc == 100 || profile_idc == 110 ||
     |    |    |   profile_idc == 122 || profile_idc == 244 ||
     |    |    |   profile_idc == 44  || profile_idc == 83  ||
     |    |    |   profile_idc == 86  || profile_idc == 118 ||
     |    |    |   profile_idc == 128 || profile_idc == 138 ||
     |    |    |   profile_idc == 139 || profile_idc == 134 ||
     |    |    |   profile_idc == 135) {{
     |    |    |
     |    |    |--- chroma_fromat_idc                                                     ue(v)
     |    |    |
     |    |   [-]-- if (chroma_fromat_idc == 3)
     |    |    |    |
     |    |    |    *--- separate_colour_plane_flag                                       u(1)
     |    |    |
     |    |    |--- bit_depth_luma_minus8                                                 ue(v)
     |    |    |--- bit_depth_chroma_minus8                                               ue(v)
     |    |    |--- qpprime_y_zero_transform_bypass_flag                                  u(1)
     |    |    |--- seq_scaling_matrix_present_flag                                       u(1)
     |    |    |
     |    |   [-]-- if (seq_scaling_matrix_present_flag)
     |    |    |    |
     |    |    |   [-]-- for (i = 0; i < ( (chroma_fromat_idc != 3) ? 8 : 12 ); i++) {{
     |    |    |    |    |
     |    |    |    |    |--- seq_scaling_list_present_flag[i]                            u(1)
     |    |    |    |    |
     |    |    |    |   [-]-- if (seq_scaling_list_present_flag[i])
     |    |    |    |         |
     |    |    |    |        [-]-- if ( i < 6 )
     |    |    |    |         |    |
     |    |    |    |         |    *--- scaling_list(4x4)
     |    |    |    |         |
     |    |    |    |        [-]-- else if ( i < 6 )
     |    |    |    |              |
     |    |    |    |              *--- scaling_list(8x8)
     |    |    |    *--- }}
     |    |    |
     |    |    *--- }}
     |    |
     |    |--- log2_max_frame_num_minus4                                                  ue(v)
     |    |
     |    |--- pic_order_cnt_type                                                         ue(v)
     |    |
     |   [-]-- if (pic_order_cnt_type == 0)
     |    |    |
     |    |    *--- log2_max_pic_order_cnt_lsb_minus4                                     ue(v)
     |    |
     |   [-]-- else if (pic_order_cnt_type == 1)
     |    |    |
     |    |    |--- delta_pic_order_always_zero_flag                                      u(1)
     |    |    |--- offset_for_non_ref_pic                                                se(v)
     |    |    |--- offset_for_top_to_bottom_field                                        se(v)
     |    |    |--- num_ref_frames_in_pic_order_cnt_cycle                                 ue(v)
     |    |    |
     |    |   [-]-- for( i = 0; i < num_ref_frames_in_pic_order_cnt_cycle; i++ )
     |    |         |
     |    |         *--- offset_for_ref_frame[i]                                          se(v)
     |    |
     |    |--- max_num_ref_frames                                                         ue(v)
     |    |--- gaps_in_frame_num_value_allowed_flag                                       u(1)
     |    |--- pic_width_in_mbs_minus1                                                    ue(v)
     |    |--- pic_height_in_map_units_minus1                                             ue(v)
     |    |
     |    |--- frame_mbs_only_flag                                                        u(1)
     |    |
     |   [-]-- if (!frame_mbs_only_flag)
     |    |    |
     |    |    *-- mb_adaptive_frame_field_flag                                           u(1)
     |    |
     |    |--- direct_8x8_inference_flag                                                  u(1)
     |    |
     |    |--- frame_cropping_flag                                                        u(1)
     |    |
     |   [-]-- if (frame_cropping_flag)
     |    |    |
     |    |    |-- frame_crop_left_offset                                                 ue(1)
     |    |    |-- frame_crop_right_offset                                                ue(1)
     |    |    |-- frame_crop_top_offset                                                  ue(1)
     |    |    *-- frame_crop_bottom_offset                                               ue(1)
     |    |
     |    |--- vui_parameters_present_flag                                                u(1)
     |    |
     |   [-]-- if (vui_parameters_present_flag)
     |    |    |
     |    |    *-- vui_parameters()
     |    |
     |    |--- }}

    """


def seq_parameter_set_data(data):
    util = Util(data)

    util.u(8)
    profile_idc = util.u(8)
    constraint_set0_flag = util.u(1)
    constraint_set1_flag = util.u(1)
    constraint_set2_flag = util.u(1)
    constraint_set3_flag = util.u(1)
    constraint_set4_flag = util.u(1)

    replacements = {
        "{{ profile_idc }}": profile_idc,
        "{{ constraint_set0_flag }}": constraint_set0_flag,
        "{{ constraint_set1_flag }}": constraint_set1_flag,
        "{{ constraint_set2_flag }}": constraint_set2_flag,
        "{{ constraint_set3_flag }}": constraint_set3_flag,
        "{{ constraint_set4_flag }}": constraint_set4_flag,
    }

    template = seq_parameter_set_data_description.__doc__
    assert isinstance(template, str)

    for key, value in replacements.items():
        template = template.replace(f"{key}", str(value))

    return template


with open("/home/lzq/stream_0.h264", "rb") as f:
    data = f.read()

for pos in enum_nals(data):
    nal_type = data[pos] & 0x1F
    if nal_type == 7:
        a = seq_parameter_set_data(data[pos:])
        print(a)
        print("sps")
    elif nal_type == 8:
        print("pps")
