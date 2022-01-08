import numpy as np
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QDialog
from mainui import Ui_MainWindow
from exerror import Ui_Dialog as ExportErrorsUi
import json
import random
import os
from pandas import DataFrame, read_feather


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        with open("datasets/data.json", encoding="utf-8") as f:
            self.data = json.load(f)
        self.q_list = []
        self.data_size = len(self.data)

        # 将各个按键和标签分组
        self.options_radioButtons = [self.ui.radioButton_A, self.ui.radioButton_B, self.ui.radioButton_C,
                                     self.ui.radioButton_D]
        self.options_checkButtons = [self.ui.checkBox_A, self.ui.checkBox_B, self.ui.checkBox_C,
                                     self.ui.checkBox_D]
        self.options_label = [self.ui.label_A, self.ui.label_B, self.ui.label_C, self.ui.label_D]

        # 设置Label的点击事件
        self.ui.label_A.mouseReleaseEvent = lambda x: self.set_option(0)
        self.ui.label_B.mouseReleaseEvent = lambda x: self.set_option(1)
        self.ui.label_C.mouseReleaseEvent = lambda x: self.set_option(2)
        self.ui.label_D.mouseReleaseEvent = lambda x: self.set_option(3)

        self.ui.action_export_error.triggered.connect(self.show_export_error)

        self.qid = None
        self.q_index = -1
        self.ui.pushButton.clicked.connect(self.submit_answer)
        self.ui.pushButton_next.clicked.connect(self.next_question)
        self.ui.pushButton_previous.clicked.connect(self.previous_question)
        self.closeEvent = lambda x: self.save()
        self.ui.pushButton_previous.setDisabled(True)
        self.is_submitted = False
        if os.path.exists("data"):
            self.foot = read_feather("data")
        else:
            self.foot = DataFrame({
                "view": np.zeros(self.data_size),
                "error": np.zeros(self.data_size)
            })
            self.foot.to_feather("data")
        self.next_question()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """
        键盘事件
        :param event:
        :return:
        """
        if event.key() == Qt.Key_Right:
            if self.ui.pushButton_next.isEnabled():
                self.next_question()
        elif event.key() == Qt.Key_Left:
            if self.ui.pushButton_previous.isEnabled():
                self.previous_question()
        elif event.key() == Qt.Key_Return:
            if self.ui.pushButton.isEnabled():
                self.submit_answer()
            elif self.ui.pushButton_next.isEnabled():
                self.next_question()
        elif event.key() == Qt.Key_A:
            self.set_option(0)
        elif event.key() == Qt.Key_B:
            self.set_option(1)
        elif event.key() == Qt.Key_C:
            self.set_option(2)
        elif event.key() == Qt.Key_D:
            self.set_option(3)

    @staticmethod
    def set_objs_visible(x, visible=False):
        for i in x:
            i.setVisible(visible)

    def clear_option(self):
        """
        清空选项
        :return:
        """
        if len(self.data[self.qid]["answer"]) == 1:
            for i in self.options_radioButtons:
                i.setChecked(False)
        else:
            for i in self.options_checkButtons:
                i.setChecked(False)

    def set_option(self, option):
        if type(option) == int:
            option = [option]
        if len(self.data[self.qid]["answer"]) == 1:
            for i in option:
                self.options_radioButtons[i].setChecked(True)
        else:
            for i in option:
                self.options_checkButtons[i].setChecked(not self.options_checkButtons[i].isChecked())

    def show_question(self, x):
        """
        显示题目，默认不显示答案
        :param x:
        :return:
        """
        self.qid = x
        if len(self.data[x]["answer"]) == 1:
            self.set_objs_visible(self.options_radioButtons, True)
            self.set_objs_visible(self.options_checkButtons, False)
            self.options_checkButtons[0].setChecked(True)
        else:
            self.set_objs_visible(self.options_radioButtons, False)
            self.set_objs_visible(self.options_checkButtons, True)
        self.clear_option()

        self.ui.label_content.setText(self.data[x]["context"])
        for i, j in zip(self.options_label, self.data[x]["option"]):
            i.setText(j)

        self.ui.label_answer.setVisible(False)

    def save(self):
        print("saving!!!")
        self.foot.to_feather("data")

    def next_question(self):
        self.q_index += 1
        if self.q_index == 0:
            self.ui.pushButton_previous.setDisabled(True)
        else:
            self.ui.pushButton_previous.setDisabled(False)
        if self.q_index == len(self.q_list):
            weights = 5 / np.exp(1 + self.foot["view"].to_numpy()) + 2 * self.foot["error"].to_numpy()
            qid = random.choices(list(range(self.data_size)), weights)[0]
            self.q_list.append({"id": qid, "choice": []})
            self.show_question(qid)

            self.is_submitted = False
            self.ui.pushButton_next.setDisabled(True)
            self.ui.pushButton.setDisabled(False)
            self.ui.lcdNumber_total.display(f"{len(self.q_list):03d}")

        else:
            qid = self.q_list[self.q_index]["id"]
            self.show_question(qid)
            if not self.is_submitted and self.q_index == len(self.q_list) - 1:
                self.ui.pushButton_next.setDisabled(True)
                self.ui.pushButton.setDisabled(False)

            else:
                if len(self.data[self.qid]["answer"]) == 1:
                    self.clear_option()
                    self.set_option(self.q_list[self.q_index]["choice"])
                else:
                    self.clear_option()
                    self.set_option(self.q_list[self.q_index]["choice"])
                self.show_answer()
        self.ui.lcdNumber_index.display(f"{self.q_index + 1:03d}")

    def get_answer(self):
        """
        获取当前作答答案
        :return:
        """
        ans = []
        if len(self.data[self.qid]["answer"]) == 1:
            for i, j in enumerate(self.options_radioButtons):
                if j.isChecked():
                    ans.append(i)
        else:
            for i, j in enumerate(self.options_checkButtons):
                if j.isChecked():
                    ans.append(i)
        return ans

    def previous_question(self):
        self.q_index -= 1
        if self.q_index == 0:
            self.ui.pushButton_previous.setDisabled(True)
        qid = self.q_list[self.q_index]["id"]
        self.show_question(qid)
        if len(self.data[self.qid]["answer"]) == 1:
            self.clear_option()
            self.set_option(self.q_list[self.q_index]["choice"])
        else:
            self.clear_option()
            self.set_option(self.q_list[self.q_index]["choice"])
        self.show_answer()
        self.ui.pushButton_next.setDisabled(False)
        self.ui.pushButton.setDisabled(True)
        self.ui.lcdNumber_index.display(f"{self.q_index + 1:03d}")

    def show_answer(self):
        self.ui.label_answer.setVisible(True)
        ans = set(self.get_answer())
        self.q_list[self.q_index]["choice"] = self.get_answer()
        ans_text = "".join([chr(i + ord('A')) for i in self.data[self.qid]["answer"]])
        ans_text = "答案：" + ans_text
        if "knowledge" in self.data[self.qid].keys():
            ans_text = ans_text + f"\t知识点：{self.data[self.qid]['knowledge']}"
        self.ui.label_answer.setText(ans_text)
        if ans == set(self.data[self.qid]["answer"]):
            self.ui.label_answer.setText("正确✔ " + ans_text)
        else:
            self.ui.label_answer.setText("错误❌ " + ans_text)

    def submit_answer(self):
        self.is_submitted = True
        self.ui.pushButton_next.setDisabled(False)
        self.ui.pushButton.setDisabled(True)

        self.show_answer()
        ans = set(self.get_answer())

        self.foot.loc[self.qid, "view"] += 1
        if ans != set(self.data[self.qid]["answer"]):
            self.foot.loc[self.qid, "error"] += 1

    def show_export_error(self):
        dialog = ExportErrorsDialog(self)
        dialog.show()
        if dialog.exec_():
            print("OK")
        else:
            print("Cancel")


class ExportErrorsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = ExportErrorsUi()
        self.ui.setupUi(self)
