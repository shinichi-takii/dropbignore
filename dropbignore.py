# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Shinichi Takii
#
# This utility is released under the MIT License: https://opensource.org/licenses/mit-license.php

"""Set to ignore Dropbox folders"""

import glob
import logging
import os
import re
import xattr

from pathlib import Path


class DropboxIgnore():
    """
    Dropbox 同期除外パス設定 クラス

    Reference:
        [Dropbox ファイルやフォルダを「無視」に設定する | Dropbox ヘルプ](https://help.dropbox.com/ja-jp/files-folders/restore-delete/ignored-files)

    Note:
        - Supported OS: macOS
        - Supported object type: Directory only (File is not support)
    """

    # ロギング レベル (DEBUG|INFO)
    _LOG_LEVEL = logging.INFO

    # ignore ファイル名
    _IGNORE_FILE_NAME = '.dropbignore'

    # 絶対に同期除外対象とするパターン
    _ABSOLUTE_IGNORE_PETTERNS = [
        '.dropbox.cache/',
    ]

    # Dropbox ignore 拡張ファイル属性 名称/値
    _IGNORE_XATTR_KEY = 'com.dropbox.ignored'
    _IGNORE_XATTR_VALUE = '1'.encode()


    def __init__(self):
        super().__init__()

        # ロギング設定
        self._logger = logging.getLogger(__name__)

        if len(self._logger.handlers) <= 0:
            self._logformat = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

            handler = logging.StreamHandler()
            handler.setLevel(self._LOG_LEVEL)
            handler.setFormatter(self._logformat)
            self._logger.setLevel(self._LOG_LEVEL)
            self._logger.addHandler(handler)
            self._logger.propagate = False


        self._init_ishidden = glob._ishidden
        self._ignore_patterns = []

        # Dropbox ルート ディレクトリ
        self._dropbox_base_path = Path(os.environ['HOME']) / 'Dropbox'

        # Dropbox ignore ファイルパス
        self._ignore_file_path = self._dropbox_base_path / self._IGNORE_FILE_NAME

        # Dropbox 検索ルート ファイルパス
        self._dropbox_path = self._dropbox_base_path

        # DEBUG:
        self._logger.debug(f"[base path] {self._dropbox_base_path}")
        self._logger.debug(f"[ignore file] {self._ignore_file_path}")
        self._logger.debug(f"[search path] {self._dropbox_path}")


    def __del__(self):
        glob._ishidden = self._init_ishidden


    def _read_ignore_patterns(self) -> list:
        """
        ignore ファイルから、同期除外パターン フィルタを取得

        Returns:
            list: 同期除外パターン
        """

        if not self._ignore_file_path.exists():
            self._logger.error(f"ignore file does not exist : '{self._IGNORE_FILE_NAME}'")

        ignore_pattern_text = self._ignore_file_path.read_text()
        ignore_patterns_base = ignore_pattern_text.split("\n")
        ignore_patterns = []

        # 有効なフィルタパターンを抽出
        #   コメント行・空白行を無視する
        invalid_filter_regex = re.compile(r"^( *)?(#.*)?$")
        for ignore_pattern in ignore_patterns_base:
            if not re.match(invalid_filter_regex, ignore_pattern):
                ignore_patterns.append(ignore_pattern)

        # DEBUG:
        # if self._logger.level <= logging.DEBUG:
        #     for ignore_pattern in ignore_patterns:
        #         self._logger.debug(f"[ignore pattern (before fix)] {ignore_pattern}")


        if len(ignore_patterns) < 1:
            self._logger.error(f"No valid patterns exist in ignore file : '{self._IGNORE_FILE_NAME}'")

        # パターン リスト 重複排除
        self._ignore_patterns = set(ignore_patterns + self._ABSOLUTE_IGNORE_PETTERNS)

        # DEBUG:
        if self._logger.level <= logging.DEBUG:
            for ignore_pattern in self._ignore_patterns:
                self._logger.debug(f"[ignore pattern] {ignore_pattern}")

        return self._ignore_patterns


    def _search_ignore_path(self):
        """
        同期除外・復活パスを探索し、リストを作成する

        - 同期除外済みパス リスト : 除外対象で、設定済みのパス
        - 同期除外パス リスト : 除外対象で、未設定のパス (除外ディレクトリ配下のパスは含めない)
        - 同期復活パス リスト : 除外設定されていて、除外対象のパス

        Note:
            探索対象 : ディレクトリのみ
        """

        # 隠しファイル (ドット ファイル) を検索対象にする
        glob._ishidden = lambda x: False

        # Dropbox 同期除外パス リスト
        self._ignore_paths = []  # 未除外
        self._ignored_paths = [] # 除外済み

        # Dropbox 同期復活パス リスト
        self._ignore_clear_paths = []

        # ディレクトリを再帰検索
        _IS_RECURSIVE = True
        serach_path = self._dropbox_path / '**'

        for subdir in glob.iglob(f"{serach_path}/", recursive=_IS_RECURSIVE):

            # 除外済みディレクトリ配下のパスは、スキップする
            if subdir.startswith(tuple(self._ignored_paths)):
                continue

            if self._IGNORE_XATTR_KEY in xattr.listxattr(subdir):
                # Dropbox 同期除外 属性あり
                # if Path(subdir).name in self._ignore_patterns:
                if self._match_ignore_pattern(Path(subdir)):
                    # 同期対象の場合、同期除外済みリストに追加
                    self._ignored_paths.append(subdir)
                else:
                    # 同期対象外の場合、同期復活リストに追加
                    self._ignore_clear_paths.append(subdir)

            # elif Path(subdir).name in self._ignore_patterns:
            elif self._match_ignore_pattern(Path(subdir)):
                # Dropbox 同期除外 属性なし & 同期対象の場合
                if not subdir.startswith(tuple(self._ignored_paths + self._ignore_paths)):
                    # 同期除外リストに親ディレクトリが含まれていなければ、同期除外リストに追加
                    self._ignore_paths.append(subdir)

        glob._ishidden = self._init_ishidden

        # DEBUG:
        if self._logger.level <= logging.DEBUG:
            for ignored_path in self._ignored_paths:
                self._logger.debug(f"[ignored path] {ignored_path}")
            for ignore_path in self._ignore_paths:
                self._logger.debug(f"[ignore path] {ignore_path}")
            for ignore_clear_path in self._ignore_clear_paths:
                self._logger.debug(f"[ignore clear path] {ignore_clear_path}")


    def _match_ignore_pattern(self, path: Path) -> bool:
        """
        同期除外対象パスを判定する

        Args:
            path (Path): 評価対象パス

        Returns:
            bool: 判定結果
                - True - 同期除外パターンと一致
                - False - 同期除外パターンと不一致
        """

        for ignore_pattern in self._ignore_patterns:
            if path.match(ignore_pattern):
                return True

        return False


    def set_ignore(self):
        """
        ディレクトリを Dropbox 同期無視に設定する
        """

        # ignore ファイルから、同期除外パターン フィルタを取得
        self._read_ignore_patterns()

        # 同期除外・復活パスを探索し、リストを作成する
        self._search_ignore_path()

        # 同期除外済みパスの情報を出力
        for ignored_path in self._ignored_paths:
            self._logger.info(f"[skip ignored] {ignored_path}")

        # 同期除外パスに Dropbox ignore 属性をセット
        for ignore_path in self._ignore_paths:
            self._logger.info(f"[set ignore] {ignore_path}")
            xattr.setxattr(ignore_path, self._IGNORE_XATTR_KEY, self._IGNORE_XATTR_VALUE)

        # 同期復活パスの Dropbox ignore 属性をクリア
        for ignore_clear_path in self._ignore_clear_paths:
            self._logger.info(f"[unset ignore] {ignore_clear_path}")
            xattr.removexattr(ignore_clear_path, self._IGNORE_XATTR_KEY)


if __name__ == "__main__":
    dropbox_ignore = DropboxIgnore()
    dropbox_ignore.set_ignore()
