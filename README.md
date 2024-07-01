１．D:/SDK/にLiDARフォルダを作成し、LiDARから得られたデータ一式を置く。その中のvideo.mp4を確認して、動画が安定しいる開始・終了秒数をメモしておく

２．スタートメニューから、iTwin Capture Modeler SDK Command Prompt – Center edition を立ち上げ（スタートメニューにない場合は検索）、 D:/SDKに移動

３.Modeler Engine Centerを立ち上げる
サインインが出たら大隈さんのアカウントでサインイン（PWはゴマ）

４． SDK Command Prompt からmodelling.pyを実行

python modelling.py –s [動画開始秒] –e [動画終了秒] –f [fps] –n [探索範囲] –l [lazファイル名(-は使わない）] –m [動画のフレーム化を行うか否か(1 or 0)]

※-m はmovieのフレーム化をすでに行っている場合0にする。

以下の流れで処理が進む
・指定fpsでphotoフォルダにフレーム出力
・フレームにブラーがあれば、前後nフレームを探索する。すべてブラーがあった場合は最も少ないフレームを選択、selectedに出力される
・軌跡の読み込み、点群の読み込み、空中三角測量、各空中三角測量結果のマージ、 再構築が行われ、D:/SDK/project にプロジェクトが保存される

４． modelling.py の実行が終了したら、D:/SDK/project /project.ccmを開く
Block_N(merge block)-Reconstruction_1-Production_1をクリックすると、下図のように、スクリプトの実行が終わってもGUI上ではproduction作成中となっている。Completedが出たら終了。
（数10分～数時間かかる）

５． D:/SDK/project /Dataの中の～.objファイルを検索して、MeshLabにドラッグアンドドロップ。
3Dモデルが表示される
（ GUI上でProduction_1を選択してResultタブを開いても見られる。）
