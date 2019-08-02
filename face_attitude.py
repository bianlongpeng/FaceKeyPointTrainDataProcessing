import cv2
import numpy as np
import os, glob

K = [6.5308391993466671e+002, 0.0, 3.1950000000000000e+002,
     0.0, 6.5308391993466671e+002, 2.3950000000000000e+002,
     0.0, 0.0, 1.0]
D = [7.0834633684407095e-002, 6.9140193737175351e-002, 0.0, 0.0, -1.3073460323689292e+000]

cam_matrix = np.array(K).reshape(3, 3).astype(np.float32)
dist_coeffs = np.array(D).reshape(5, 1).astype(np.float32)

object_pts = np.float32([[6.825897, 6.760612, 4.402142],
                         [1.330353, 7.122144, 6.903745],
                         [-1.330353, 7.122144, 6.903745],
                         [-6.825897, 6.760612, 4.402142],
                         [5.311432, 5.485328, 3.987654],
                         [1.789930, 5.393625, 4.413414],
                         [-1.789930, 5.393625, 4.413414],
                         [-5.311432, 5.485328, 3.987654],
                         [2.005628, 1.409845, 6.165652],
                         [-2.005628, 1.409845, 6.165652],
                         [2.774015, -2.080775, 5.048531],
                         [-2.774015, -2.080775, 5.048531],
                         [0.000000, -3.116408, 6.097667],
                         [0.000000, -7.415691, 4.070434]])

reprojectsrc = np.float32([[10.0, 10.0, 10.0],
                           [10.0, 10.0, -10.0],
                           [10.0, -10.0, -10.0],
                           [10.0, -10.0, 10.0],
                           [-10.0, 10.0, 10.0],
                           [-10.0, 10.0, -10.0],
                           [-10.0, -10.0, -10.0],
                           [-10.0, -10.0, 10.0]])

line_pairs = [[0, 1], [1, 2], [2, 3], [3, 0],
              [4, 5], [5, 6], [6, 7], [7, 4],
              [0, 4], [1, 5], [2, 6], [3, 7]]


# 获取头部姿态
def get_head_pose(shape):
    """
    根据14个关键点坐标计算姿态
    :param shape: 68人脸关键点坐标数组
    :return:
    """
    image_pts = np.float32([shape[17], shape[21], shape[22], shape[26], shape[36],
                            shape[39], shape[42], shape[45], shape[31], shape[35],
                            shape[48], shape[54], shape[57], shape[8]])

    _, rotation_vec, translation_vec = cv2.solvePnP(object_pts, image_pts, cam_matrix, dist_coeffs)

    reprojectdst, _ = cv2.projectPoints(reprojectsrc, rotation_vec, translation_vec, cam_matrix,
                                        dist_coeffs)

    reprojectdst = tuple(map(tuple, reprojectdst.reshape(8, 2)))

    # calc euler angle
    rotation_mat, _ = cv2.Rodrigues(rotation_vec)
    pose_mat = cv2.hconcat((rotation_mat, translation_vec))
    _, _, _, _, _, _, euler_angle = cv2.decomposeProjectionMatrix(pose_mat)

    return reprojectdst, euler_angle


def main(path):
    """
    获取并写入姿态三个数值：pitch, yaw, roll
    :param path: 待计算姿态图片路径
    :return:
    """

    if os.path.exists(path):
        # 读取图像帧
        frame = cv2.imread(path)
        # 提取关键点标签
        if os.path.splitext(os.path.basename(path))[1] == '.jpg':
            txt_path = os.path.splitext(path)[0] + ".txt"
            print(txt_path)
        num_of_line = 1
        points_68 = []
        with open(txt_path, 'r') as f:
            while True:
                line = f.readline()
                # 针对新写入坐标文件
                if num_of_line <= 3:
                    print("非坐标行")
                elif num_of_line > 3 and num_of_line < 72:
                    num = [int(float('%.3f' % float(n))) for n in line.split()]
                    points_68.append(num)
                elif num_of_line >= 72:
                    break
                num_of_line = num_of_line + 1
        shape = points_68
        # 计算头部姿态
        reprojectdst, euler_angle = get_head_pose(shape)

        for (x, y) in shape:
            cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)

            cv2.putText(frame, "X: " + "{:7.2f}".format(euler_angle[0, 0]), (20, 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.75, (0, 0, 0), thickness=2)
            cv2.putText(frame, "Y: " + "{:7.2f}".format(euler_angle[1, 0]), (20, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.75, (0, 0, 0), thickness=2)
            cv2.putText(frame, "Z: " + "{:7.2f}".format(euler_angle[2, 0]), (20, 80), cv2.FONT_HERSHEY_SIMPLEX,
                        0.75, (0, 0, 0), thickness=2)
        # 输出姿态：pitch, yaw, roll
        print("pitch: " + "{:7.2f}".format(euler_angle[0, 0]))  # 俯仰
        print("yaw: " + "{:7.2f}".format(euler_angle[1, 0]))  # 转头
        print("roll: " + "{:7.2f}".format(euler_angle[2, 0]))  # 歪头
        # 转换姿态为一行字符串
        newLine = str(float('%.3f' % float(euler_angle[0, 0]))) + \
                  ' ' + str(float('%.3f' % float(euler_angle[1, 0]))) + \
                  ' ' + str(float('%.3f' % float(euler_angle[2, 0])))
        # 将姿态数值在标签文件最后一行追加写入
        write_txt(newLine, txt_path)

def write_txt(line, output_file):
    with open(output_file, 'a') as f:
        f.write('\n')
        f.write(line)


def make_txt(rootPath):
    for fi in glob.glob(os.path.join(rootPath, "*.jpg")):
        if fi is not None:
            main(fi)
        else:
            break
    for fi in glob.glob(os.path.join(rootPath, "*.png")):
        if fi is not None:
            main(fi)
        else:
            break

if __name__ == '__main__':
    make_txt("300w/01_Indoor/")
    make_txt("300w/02_Outdoor/")
    make_txt("lfpw/trainfaceset/")
    make_txt("afw/trainfaceset/")
    make_txt("helen/trainfaceset/")