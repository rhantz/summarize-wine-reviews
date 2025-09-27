import pandas as pd
import html


class DataLoader():

    def __init__(self):
        self.file_path = "cellartracker.txt"
        self.df_ratings = self._load_df_ratings()

    @staticmethod
    def _preprocess_df_ratings(df: pd.DataFrame) -> pd.DataFrame:
        for col in ["wineId", "userId", "year", "time", "points"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        df["time"] = pd.to_datetime(df["time"], unit="s")
        return df

    def _load_df_ratings(self) -> pd.DataFrame:
        with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f: # TODO check back here
            rating_records = [
                {
                    key.split("/")[-1]: value
                    for key, value in (key_value_pair.split(": ", 1)
                    for key_value_pair in record.split("\n"))
                }
                for record in html.unescape(f.read()).split("\n\n")
            ]
        return self._preprocess_df_ratings(df=pd.DataFrame(rating_records))


if __name__ == '__main__':

    data_loader = DataLoader()
    df_ratings = data_loader.df_ratings
