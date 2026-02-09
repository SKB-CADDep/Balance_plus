import pandas as pd
import json
import os
import datetime
import hashlib
import re
import getpass
from pathlib import Path
from typing import List, Dict, Type

# --- НАСТРОЙКИ ---
PARSER_TREU_VERSION = "2.2.0"

# --- ИМПОРТ SEUIF97 ---
try:
    from seuif97 import *

    SEUIF_AVAILABLE = True
except ImportError:
    SEUIF_AVAILABLE = False


    def ph(*args):
        return None


    def ps(*args):
        return None


    def pt(*args):
        return None

try:
    import openpyxl
except ImportError:
    openpyxl = None


# ==========================================
# УТИЛИТЫ
# ==========================================
class DataUtils:
    @staticmethod
    def clean(value):
        if pd.isna(value) or value is None: return None
        s_value = str(value).strip()
        if s_value == "": return None
        try:
            clean_num_str = s_value.replace(',', '.')
            float_val = float(clean_num_str)
            if float_val.is_integer(): return int(float_val)
            return float_val
        except ValueError:
            return s_value


# ==========================================
# ГЕНЕРАТОР ЕДИНИЦ ИЗМЕРЕНИЯ
# ==========================================
class SystemUnitsGenerator:
    CONFIG = {
        "dimension": {
            "unit": "мм",
            "values": ["lсл", "Dср_сл", "lрл", "Dср_рл", "dу", "Dу", "dуэ", "dб", "dбэ"]
        },
        "square": {
            "unit": "м2",
            "values": ["Fсл", "Fрл", "Fo", "Fs"]
        },
        "dimensionless": {
            "unit": "-",
            "values": ["e", "sin_a_эф", "sin_b_2", "x0", "x1", "x2", "U/C0", "ro_ср", "КПД_u", "КПД_i", "fi", "psi",
                       "mu_сл", "mu_рл", "muсл", "G_д_у", "muрл", "rk", "G_б_у", "r_к", "rд", "rщ", "r_ср"]
        },
        "mass_flow": {
            "unit": "т/ч",
            "values": ["Gотс", "Gсл", "Gрл", "Gst", "Gdel", "Gупл", "Gсеп"]
        },
        "enthalpy": {
            "unit": "ккал/кг",
            "values": ["H0", "hад", "hвых", "h0", "hu", "hi", "H2", "H1", "ifs", "i1s", "i2s", "ifss", "i1ss", "i2ss",
                       "i3", "i0ss", "hсл", "h0'", "hрл", "h''", "h0''"]
        },
        "pressure": {
            "unit": "кгс/см2",
            "values": ["P0", "P1", "P2", "p2s", "P'ф", "Pкр'", "P''ф", "Pкр''", "P''2", "P'2"]
        },
        "temperature": {
            "unit": "°C",
            "values": ["t0", "t1", "t2"]
        },
        "power": {
            "unit": "МВт",
            "values": ["Nu", "Ni"]
        },
        "specific_volume": {
            "unit": "м3/кг",
            "values": ["v2s", "v3", "v0ss", "v'ф", "v1", "vкр'", "v''ф", "v2", "vкр''"]
        },
        "enthropy": {
            "unit": "ккал/кгК",
            "values": ["s1ss", "s1s", "s2s"]
        },
        "speed": {
            "unit": "м/с",
            "values": ["С1t", "С1", "С1u", "C1a", "W1u", "W1", "W1*", "U", "W2t", "W2", "W2u", "W2a", "C2u", "C2"]
        },
        "angle": {
            "unit": "град",
            "values": ["b1"]
        },
        "GV": {
            "unit": "м3/с",
            "values": ["GV2"]
        }
    }

    @staticmethod
    def get() -> dict:
        return SystemUnitsGenerator.CONFIG


# ==========================================
# ПАРСЕРЫ
# ==========================================

class MetaDataParser:
    def parse(self, file_path: Path, df_main_results: pd.DataFrame = None) -> dict:
        stats = file_path.stat()
        try:
            date_found = datetime.datetime.fromtimestamp(stats.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        except:
            date_found = None
        try:
            date_modified = datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except:
            date_modified = None
        user_found = None
        if file_path.suffix.lower() == ".xlsx" and openpyxl:
            try:
                wb = openpyxl.load_workbook(file_path, read_only=True)
                user_found = wb.properties.creator
                wb.close()
            except:
                pass
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            current_user = getpass.getuser()
        except:
            current_user = os.environ.get("USERNAME") or "Unknown"
        zone_name = ""
        if df_main_results is not None and not df_main_results.empty:
            try:
                raw_text = str(df_main_results.iloc[6, 1])
                match = re.search(r"Исходные данные:\s*(.*?);", raw_text)
                if match:
                    zone_name = match.group(1).strip()
                else:
                    zone_name = raw_text.split(';')[0].replace("REGIM: Исходные данные:", "").strip()
            except:
                pass
        file_hash = self._calculate_md5(file_path)
        file_size_kb = round(stats.st_size / 1024, 2)
        mode_name = file_path.parent.name
        file_name = file_path.name
        return {
            "mode_name": mode_name, "file_name_original_excel": file_name,
            "date_found_excel": date_found, "date_modified_excel": date_modified,
            "user_found_excel": user_found, "date_download_to_json": date_now,
            "user_download_to_json": current_user, "zone_name": zone_name,
            "project": "", "file_hash": file_hash, "file_size_kb": file_size_kb,
            "parser_version": PARSER_TREU_VERSION, "project_id": ""
        }

    def _calculate_md5(self, file_path: Path) -> str:
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""): hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return ""


class SourceDataParser:
    def parse(self, df: pd.DataFrame) -> dict:
        if df is None or df.empty or len(df) < 2: return {}
        data_dict = {}
        for col_idx in range(len(df.columns)):
            raw_key = df.iloc[0, col_idx]
            if pd.isna(raw_key) or str(raw_key).strip() == "": break
            key_name = str(raw_key).strip()
            raw_val = df.iloc[1, col_idx]
            data_dict[key_name] = DataUtils.clean(raw_val)
        return data_dict


class MainDataParser:
    def parse(self, df: pd.DataFrame) -> dict:
        result_data = {}
        if df is None or df.empty or len(df) <= 6: return {"main_information": None}
        try:
            raw_text = df.iloc[6, 1]
            if pd.isna(raw_text): return {"main_information": None}
            raw_text_str = str(raw_text).strip()
            result_data["main_information"] = raw_text_str
            parts = raw_text_str.split(';')
            for part in parts:
                part = part.strip()
                if '=' in part:
                    key_raw, val_raw = part.split('=', 1)
                    key = key_raw.strip()
                    value = DataUtils.clean(val_raw)
                    if key: result_data[key] = value
        except Exception as e:
            result_data["error"] = str(e)
        return result_data


class GeometryParser:
    COL_MAP = {
        2: "e", 3: "Fсл", 4: "lсл", 5: "sin_a_эф", 6: "Dср_сл",
        7: "Fрл", 8: "lрл", 9: "sin_b_2", 10: "Dср_рл", 11: "zу",
        12: "dу", 13: "Dу", 14: "dуэ", 15: "zб", 16: "dб",
        17: "dбэ", 18: "DU_type", 19: "BU_type", 20: "NL_profile",
        21: "RL_profile"
    }

    def parse(self, df: pd.DataFrame) -> dict:
        geometry_dict = {}
        START_ROW = 10;
        STAGE_COL = 1
        if df is None or df.empty or len(df) <= START_ROW: return {}
        for row_idx in range(START_ROW, len(df)):
            try:
                raw_stage = df.iloc[row_idx, STAGE_COL]
                if pd.isna(raw_stage): break
                stage_val = DataUtils.clean(raw_stage)
                if stage_val is None: break
                stage_key = str(stage_val)
                stage_params = {}
                for col_idx, param_name in self.COL_MAP.items():
                    if col_idx < len(df.columns):
                        val = DataUtils.clean(df.iloc[row_idx, col_idx])
                        stage_params[param_name] = val
                    else:
                        stage_params[param_name] = None
                geometry_dict[stage_key] = stage_params
            except Exception:
                continue
        return geometry_dict


class MainResultsParser:
    COL_MAP = {
        2: "Gотс", 3: "H0", 4: "P0", 5: "t0", 6: "x0",
        7: "P2", 8: "hад", 9: "hвых", 10: "h0", 11: "U/C0",
        12: "GV2", 13: "ro_ср", 14: "hu", 15: "КПД_u",
        16: "Nu", 17: "hi", 18: "КПД_i", 19: "Ni",
        23: "Gсл", 24: "Gрл"
    }

    def parse(self, df: pd.DataFrame) -> dict:
        results_dict = {}
        START_ROW = 10;
        STAGE_COL = 1
        if df is None or df.empty or len(df) <= START_ROW: return {}
        for row_idx in range(START_ROW, len(df)):
            try:
                raw_stage = df.iloc[row_idx, STAGE_COL]
                if pd.isna(raw_stage): break
                stage_val = DataUtils.clean(raw_stage)
                if stage_val is None: break
                stage_key = str(stage_val)
                stage_params = {}
                for col_idx, param_name in self.COL_MAP.items():
                    if col_idx < len(df.columns):
                        val = DataUtils.clean(df.iloc[row_idx, col_idx])
                        stage_params[param_name] = val
                    else:
                        stage_params[param_name] = None
                results_dict[stage_key] = stage_params
            except Exception:
                continue
        return results_dict


class LossesParser:
    COL_MAP = {
        2: "fi", 3: "dh_сл", 4: "psi", 5: "dh_рл", 6: "dh_вых",
        7: "dh_бу", 8: "dh_ду", 9: "dh_вык", 10: "dh_трен", 11: "dh_пров",
        12: "dh_x", 15: "mu_сл", 16: "mu_рл", 17: "ifs", 18: "i1s", 19: "i2s",
        20: "ifss", 21: "i1ss", 22: "i2ss", 23: "v2s", 24: "i3",
        25: "v3", 26: "v0ss", 27: "i0ss", 28: "s1ss", 29: "s1s",
        30: "p2s", 31: "s2s", 32: "fir1", 33: "fir2", 34: "v1ss_g",
        35: "value_1", 36: "value_2"
    }

    def parse(self, df: pd.DataFrame) -> dict:
        losses_dict = {}
        START_ROW = 10;
        STAGE_COL = 1
        if df is None or df.empty or len(df) <= START_ROW: return {}
        for row_idx in range(START_ROW, len(df)):
            try:
                raw_stage = df.iloc[row_idx, STAGE_COL]
                if pd.isna(raw_stage): break
                stage_val = DataUtils.clean(raw_stage)
                if stage_val is None: break
                stage_key = str(stage_val)
                stage_params = {}
                for col_idx, param_name in self.COL_MAP.items():
                    if col_idx < len(df.columns):
                        val = DataUtils.clean(df.iloc[row_idx, col_idx])
                        stage_params[param_name] = val
                    else:
                        stage_params[param_name] = None
                losses_dict[stage_key] = stage_params
            except Exception:
                continue
        return losses_dict


class NozzleBladesParser:
    COL_MAP = {
        2: "P'ф", 3: "v'ф", 4: "hсл", 5: "h0'", 6: "С1t",
        7: "С1", 8: "С1u", 9: "C1a", 10: "W1u", 11: "W1",
        12: "W1*", 13: "b1", 14: "P1", 15: "v1", 16: "Pкр'",
        17: "vкр'", 18: "muсл", 19: "sin(b1+d')", 20: "B(fiр)",
        21: "G_д_у", 22: "Gst", 23: "Gdel", 24: "Gупл",
        25: "Gсеп", 26: "гамма", 27: "cкр", 28: "PoteryH"
    }

    def parse(self, df: pd.DataFrame) -> dict:
        nozzle_dict = {}
        START_ROW = 10;
        STAGE_COL = 1
        if df is None or df.empty or len(df) <= START_ROW: return {}
        for row_idx in range(START_ROW, len(df)):
            try:
                raw_stage = df.iloc[row_idx, STAGE_COL]
                if pd.isna(raw_stage): break
                stage_val = DataUtils.clean(raw_stage)
                if stage_val is None: break
                stage_key = str(stage_val)
                stage_params = {}
                for col_idx, param_name in self.COL_MAP.items():
                    if col_idx < len(df.columns):
                        val = DataUtils.clean(df.iloc[row_idx, col_idx])
                        stage_params[param_name] = val
                    else:
                        stage_params[param_name] = None
                nozzle_dict[stage_key] = stage_params
            except Exception:
                continue
        return nozzle_dict


class WorkingBladesParser:
    COL_MAP = {
        2: "P''ф", 3: "v''ф", 4: "U", 5: "hрл", 6: "h''",
        7: "h0''", 8: "W2t", 9: "W2", 10: "W2u", 11: "W2a",
        12: "C2u", 13: "C2", 14: "v2", 15: "x2", 16: "Pкр''",
        17: "vкр''", 18: "muрл", 19: "sin(b2+d'')", 20: "rk",
        21: "G_б_у", 22: "value_1", 23: "value_2", 24: "value_3",
        25: "value_4"
    }

    def parse(self, df: pd.DataFrame) -> dict:
        working_dict = {}
        START_ROW = 10;
        STAGE_COL = 1
        if df is None or df.empty or len(df) <= START_ROW: return {}
        for row_idx in range(START_ROW, len(df)):
            try:
                raw_stage = df.iloc[row_idx, STAGE_COL]
                if pd.isna(raw_stage): break
                stage_val = DataUtils.clean(raw_stage)
                if stage_val is None: break
                stage_key = str(stage_val)
                stage_params = {}
                for col_idx, param_name in self.COL_MAP.items():
                    if col_idx < len(df.columns):
                        val = DataUtils.clean(df.iloc[row_idx, col_idx])
                        stage_params[param_name] = val
                    else:
                        stage_params[param_name] = None
                working_dict[stage_key] = stage_params
            except Exception:
                continue
        return working_dict


class AxialForceParser:
    COL_MAP = {
        2: "Gк", 3: "P0", 4: "P''2", 5: "P'2", 6: "Dср_рл",
        7: "lрл", 8: "dlб", 9: "Dу", 10: "dу/D''у", 11: "dш/D'у",
        12: "dо/Nдв", 13: "zо/Nдн", 14: "sin_a_1э", 15: "r_к",
        16: "a", 17: "b", 18: "k", 19: "rд", 20: "rщ",
        21: "h", 22: "r_ср", 23: "Nсл", 24: "Nрл", 25: "Nуст",
        26: "Nсум", 27: "Fo", 28: "Fs"
    }

    def parse(self, df: pd.DataFrame) -> dict:
        axial_dict = {}
        START_ROW = 10;
        STAGE_COL = 1
        if df is None or df.empty or len(df) <= START_ROW: return {}
        for row_idx in range(START_ROW, len(df)):
            try:
                raw_stage = df.iloc[row_idx, STAGE_COL]
                if pd.isna(raw_stage): continue
                stage_str = str(raw_stage).strip()
                if "Т-Н" not in stage_str: continue
                clean_stage_key = stage_str.replace("Т-Н", "").strip()
                if not clean_stage_key: continue
                stage_params = {}
                for col_idx, param_name in self.COL_MAP.items():
                    if col_idx < len(df.columns):
                        val = DataUtils.clean(df.iloc[row_idx, col_idx])
                        stage_params[param_name] = val
                    else:
                        stage_params[param_name] = None
                axial_dict[clean_stage_key] = stage_params
            except Exception:
                continue
        return axial_dict


class FlowPathParser:
    COL_MAP = {
        2: "Профиль'", 3: "D'к", 4: "L'", 5: "B'к", 6: "z'",
        7: "α'уст", 8: "F'вых", 9: "Профиль''", 10: "D''к",
        11: "L''", 12: "B''к", 13: "z''", 14: "α''уст",
        15: "F''вых", 16: "Профиль хв-ка"
    }

    def parse(self, df: pd.DataFrame) -> dict:
        flow_dict = {}
        START_ROW = 10;
        STAGE_COL = 1
        if df is None or df.empty or len(df) <= START_ROW: return {}
        for row_idx in range(START_ROW, len(df)):
            try:
                raw_stage = df.iloc[row_idx, STAGE_COL]
                if pd.isna(raw_stage): break
                stage_val = DataUtils.clean(raw_stage)
                if stage_val is None: break
                stage_key = str(stage_val)
                stage_params = {}
                for col_idx, param_name in self.COL_MAP.items():
                    if col_idx < len(df.columns):
                        val = DataUtils.clean(df.iloc[row_idx, col_idx])
                        stage_params[param_name] = val
                    else:
                        stage_params[param_name] = None
                flow_dict[stage_key] = stage_params
            except Exception:
                continue
        return flow_dict


# ==========================================
# ГЛАВНЫЙ ПРОЦЕССОР
# ==========================================
class ExcelProcessor:
    def __init__(self):
        self.meta_parser = MetaDataParser()
        self.source_parser = SourceDataParser()
        self.main_parser = MainDataParser()
        self.geometry_parser = GeometryParser()
        self.main_results_parser = MainResultsParser()
        self.losses_parser = LossesParser()
        self.nozzle_parser = NozzleBladesParser()
        self.working_parser = WorkingBladesParser()
        self.axial_parser = AxialForceParser()
        self.flow_path_parser = FlowPathParser()
        self.units_generator = SystemUnitsGenerator()

    def process_root_directory(self, root_folder_path: str):
        root_path = Path(root_folder_path)
        if not root_path.exists():
            print(f"Папка не найдена: {root_path}")
            return
        print(f"--- Старт сканирования корневой директории: {root_path} ---")
        subfolders = [f for f in root_path.iterdir() if f.is_dir()]
        if not subfolders:
            print("Подпапки не найдены.")
            return
        for folder in subfolders:
            self._process_subfolder(folder, root_path)

    def _post_process_data(self, folder_data: dict):
        """Расчеты, доп. параметры и конвертация единиц."""

        # 1. AXIAL FORCE
        for params in folder_data["axial_force"].values():
            for key in ["Nсл", "Nрл", "Nуст", "Nсум"]:
                if params.get(key) is not None:
                    try:
                        params[key] = round(params[key] / 9.80665, 4)
                    except:
                        pass

        # 2. MAIN RESULTS (Досчет)
        # Gотс * 3.6
        for res in folder_data["main_results"].values():
            if res.get("Gотс") is not None:
                try:
                    res["Gотс"] = round(res["Gотс"] * 3.6, 4)
                except:
                    pass

        TO_MPA = 0.0980665
        TO_KJ = 4.1868

        for stage_key, res in folder_data["main_results"].items():
            nozzle = folder_data["nozzle_blades"].get(stage_key, {})
            losses = folder_data["losses"].get(stage_key, {})

            p1 = nozzle.get("P1")
            res["P1"] = p1
            h2 = losses.get("i2ss")
            res["H2"] = h2

            h0 = res.get("H0")
            hi = res.get("hi")
            ro_sr = res.get("ro_ср")
            h1 = None
            if all(v is not None for v in [h0, hi, ro_sr]):
                try:
                    h1 = h0 - hi * (1 - 0.01 * ro_sr)
                    res["H1"] = round(h1, 4)
                except:
                    pass
            else:
                res["H1"] = None

            t1, x1 = None, None
            if p1 is not None and h1 is not None:
                try:
                    t1 = ph(p1 * TO_MPA, h1 * TO_KJ, 1)
                    x1 = ph(p1 * TO_MPA, h1 * TO_KJ, 15)
                    if t1 is not None: t1 = round(t1, 4)
                    if x1 is not None: x1 = round(x1, 6)
                except:
                    pass
            res["t1"] = t1;
            res["x1"] = x1

            p2 = res.get("P2")
            t2, x2 = None, None
            if p2 is not None and h2 is not None:
                try:
                    t2 = ph(p2 * TO_MPA, h2 * TO_KJ, 1)
                    x2 = ph(p2 * TO_MPA, h2 * TO_KJ, 15)
                    if t2 is not None: t2 = round(t2, 4)
                    if x2 is not None: x2 = round(x2, 6)
                except:
                    pass
            res["t2"] = t2;
            res["x2"] = x2

        # 3. КОНВЕРТАЦИЯ ЕДИНИЦ
        def apply_conv(data_dict, keys, op):
            for params in data_dict.values():
                for k in keys:
                    if params.get(k) is not None:
                        try:
                            params[k] = round(op(params[k]), 6)
                        except:
                            pass

        apply_conv(folder_data["geometry"], ["Fсл", "Fрл"], lambda x: x / 100)
        apply_conv(folder_data["geometry"], ["e"], lambda x: x / 100)

        apply_conv(folder_data["main_results"], ["Gсл", "Gрл"], lambda x: x * 3.6)
        apply_conv(folder_data["main_results"], ["ro_ср", "КПД_u", "КПД_i"], lambda x: x / 100)
        apply_conv(folder_data["main_results"], ["Nu", "Ni"], lambda x: x / 1000)

        dh_keys = ["dh_сл", "dh_рл", "dh_вых", "dh_бу", "dh_ду", "dh_вык", "dh_трен", "dh_пров", "dh_x"]
        apply_conv(folder_data["losses"], dh_keys, lambda x: x / 100)
        apply_conv(folder_data["losses"], ["s1ss", "s1s", "s2s"], lambda x: x / 4.1868)

        apply_conv(folder_data["nozzle_blades"], ["v'ф", "v1", "vкр'"], lambda x: x / 1000)
        apply_conv(folder_data["nozzle_blades"], ["G_д_у"], lambda x: x / 100)
        apply_conv(folder_data["nozzle_blades"], ["Gst", "Gdel", "Gупл", "Gсеп"], lambda x: x * 3.6)

        apply_conv(folder_data["working_blades"], ["v''ф", "v2", "vкр''"], lambda x: x / 1000)
        apply_conv(folder_data["working_blades"], ["rk", "G_б_у"], lambda x: x / 100)

        apply_conv(folder_data["axial_force"], ["Fo", "Fs"], lambda x: x / 10000)
        apply_conv(folder_data["axial_force"], ["r_к", "rд", "rщ", "r_ср"], lambda x: x / 100)

    def _process_subfolder(self, subfolder_path: Path, output_root: Path):
        print(f"\n>>> Обработка подпапки: {subfolder_path.name}")

        folder_data = {
            "meta_data": [], "source_data": [], "main_data": [],
            "geometry": {}, "main_results": {}, "losses": {},
            "nozzle_blades": {}, "working_blades": {},
            "axial_force": {}, "flow_path": {},
            "system_units": self.units_generator.get()
        }

        excel_files = []
        for ext in ["*.xlsx", "*.xls", "*.xlsm"]:
            excel_files.extend(subfolder_path.glob(ext))

        if not excel_files:
            print(f"    Нет Excel файлов, пропускаем.")
            return

        for file_path in excel_files:
            if file_path.name.startswith("~$"): continue
            try:
                xls = pd.read_excel(file_path, sheet_name=None, header=None, dtype=object)
                sheet_main = xls.get("Основн. результаты")
                folder_data["meta_data"].append(self.meta_parser.parse(file_path, sheet_main))
                folder_data["main_data"].append(self.main_parser.parse(sheet_main))
                folder_data["source_data"].append(self.source_parser.parse(xls.get("Исх. данные")))
                if xls.get("Геом. данные") is not None:
                    folder_data["geometry"].update(self.geometry_parser.parse(xls.get("Геом. данные")))
                if sheet_main is not None:
                    folder_data["main_results"].update(self.main_results_parser.parse(sheet_main))
                if xls.get("Потери") is not None:
                    folder_data["losses"].update(self.losses_parser.parse(xls.get("Потери")))
                if xls.get("Напр.лопатки") is not None:
                    folder_data["nozzle_blades"].update(self.nozzle_parser.parse(xls.get("Напр.лопатки")))
                if xls.get("Раб. лопатки") is not None:
                    folder_data["working_blades"].update(self.working_parser.parse(xls.get("Раб. лопатки")))
                if xls.get("Осевое усилие") is not None:
                    folder_data["axial_force"].update(self.axial_parser.parse(xls.get("Осевое усилие")))
                if xls.get("Проточная часть") is not None:
                    folder_data["flow_path"].update(self.flow_path_parser.parse(xls.get("Проточная часть")))
            except Exception as e:
                print(f"    [ERROR] Ошибка в файле {file_path.name}: {e}")

        if not folder_data["meta_data"]: return

        # ПОСТ-ОБРАБОТКА
        self._post_process_data(folder_data)

        # СОРТИРОВКА СТУПЕНЕЙ
        def sort_dict(d):
            if not d: return d
            try:
                return dict(sorted(d.items(), key=lambda item: int(item[0])))
            except ValueError:
                return dict(sorted(d.items()))

        for key in ["geometry", "main_results", "losses", "nozzle_blades",
                    "working_blades", "axial_force", "flow_path"]:
            folder_data[key] = sort_dict(folder_data[key])

        # --- СОРТИРОВКА ПАРАМЕТРОВ В MAIN_RESULTS (Новое) ---
        MAIN_RESULTS_ORDER = [
            "Gотс", "Gсл", "Gрл", "P0", "H0", "t0", "x0", "P1", "H1", "t1", "x1",
            "P2", "H2", "t2", "x2", "hад", "hвых", "h0", "U/C0", "GV2", "ro_ср",
            "hu", "КПД_u", "Nu", "hi", "КПД_i", "Ni"
        ]

        main_res_block = folder_data["main_results"]
        for stage, params in main_res_block.items():
            sorted_params = {}
            # 1. Сначала добавляем параметры в нужном порядке
            for key in MAIN_RESULTS_ORDER:
                if key in params:
                    sorted_params[key] = params[key]
            # 2. Добавляем остальные, которых нет в списке (чтобы не потерять)
            for key, val in params.items():
                if key not in sorted_params:
                    sorted_params[key] = val
            main_res_block[stage] = sorted_params

        # СОХРАНЕНИЕ
        project_id = "0"
        date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        json_dump_str = json.dumps(folder_data, sort_keys=True)
        content_hash = hashlib.md5(json_dump_str.encode('utf-8')).hexdigest()
        file_name = f"{project_id}_{date_str}_{content_hash}.json"
        output_file = output_root / file_name

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # json.dump запишет словари в том порядке, в котором мы их собрали
                json.dump(folder_data, f, ensure_ascii=False, indent=4)
            print(f"    [OK] JSON создан: {file_name}")
        except Exception as e:
            print(f"    [ERROR] Не удалось сохранить: {e}")


# ==========================================
# ЗАПУСК
# ==========================================
if __name__ == "__main__":
    target_folder = r"C:\1\data_treu"

    processor = ExcelProcessor()
    processor.process_root_directory(target_folder)
