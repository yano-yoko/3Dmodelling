import cv2
import os
import ipdb

video_path='./video.mp4'#ビデオのフォルダ
photo_path ="./photo"#N個（選ばれた時に100個になるような数）の写真のフォルダ（photo_0...)
selected_path = './selected'#選ばれた（ブラーがない）写真のフォルダ(selected_0...)
start_sec=13#切り出し開始時刻
stop_sec=201#切り出し終了時刻
basename='frame'#切り出した時のファイル名（frame_〇.jpg)
fps=1/2#必要な周波数(何秒に何枚の写真が必要か）

def save_frame_range_sec(video_path, output_path, start_sec, stop_sec, basename,fps, ext='jpg'):
    cap = cv2.VideoCapture(video_path)#動画の読み込み

    if not cap.isOpened():#画像が起動できたか確認
        return
    
    digit = len(str(int(cap.get(cv2.CAP_PROP_FRAME_COUNT))))#動画の合計フレーム数の桁数

    org_fps = cap.get(cv2.CAP_PROP_FPS)#1秒当たりのフレーム数を取得
    step_sec = 1 / round(org_fps)#何秒に1枚か
    N=fps/step_sec*100#1フォルダあたり何枚にすれば、ブラーを除いたとき１００枚になるか

    sec = start_sec#開始秒
    file_cnt=0#ファイルをカウント
    dir_cnt=0#ディレクトリをカウント
    
    while sec < stop_sec:#終了秒になるまで
        
        if file_cnt%(N+1)==0:#フレームN個ごとに出力フォルダを作成(N個目の次に作成）

            print(f'making photo_{dir_cnt}')
            output_path_plus=f"{output_path}_{dir_cnt}"#~/photo_〇
            os.makedirs(output_path_plus, exist_ok=True)
            base_path = os.path.join(output_path_plus, basename)#~/photo_〇/frame_
            dir_cnt+=1
            
        n = round(org_fps * sec)#現在のフレーム位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, n)# 再生位置（フレーム位置）をｎに設定
        ret, frame = cap.read()#retは画像情報が取れたか否か、frameは画像情報
        
        if ret:#画像情報が取れてたら
            #~/photo_〇/frame_,フレーム数,.jpg の名前で画像出力
            cv2.imwrite(
                #'{}_{}_{:.2f}.{}'.format(
                #    base_path, str(n).zfill(digit), n * fps_inv, ext
                '{}_{}.{}'.format(
                    base_path, str(n).zfill(digit), ext #zfill(digit) digit桁に右寄せゼロ埋め
                ),
                frame
            )
            file_cnt+=1
        else:
            return
        sec += step_sec

    return dir_cnt

def select_high_laplacian(photo_path,selected_path,num_photo_dir):
    
    #laplacianを使ってブラーを検出
    file_count=round(len(os.listdir(f"{photo_path}_0"))/100)
    imax=int((file_count-1)/2)#前後2個までみる
    num_dir=num_photo_dir+1#写真のディレクトリの数
        
    for no in range(num_dir):

        print(f'making selected_{no}')
        r_path=f'{photo_path}_{no}/'#読み込みディレクトリ
        w_path=f'{selected_path}_{no}/'#書き込みディレクトリ
        image_file=os.listdir(r_path)#読み込みファイル
        os.makedirs(w_path, exist_ok=True)#書き込みディレクトリ作成
        #breakpoint()
        for idx in range(len(image_file)):
            
            if idx%file_count==0:#5つ飛ばしで読み込み
                lap_val_list=[]#5フレーム前後のラプラシアン値を記憶
                lap_key_list=[]#5フレーム前後の間、前(bef)と後ろ(aft)のどちらが選ばれたか記憶
                output_cnt=0#5フレームの間に画像が出力されたかチェック
                
                for i in range(imax+1):
                    
                    #idxの後ろの探索
                    #最後のフレームのidxと現在のidxの差よりiが大きくなったら、それ以上後を見られないのでその差をiとする
                    if i>len(image_file)-1-idx: p=len(image_file)-1-idx
                    else:aft=i
        
                    image_path_aft = r_path + image_file[idx+aft]
                    out_image_path = w_path + image_file[idx+aft]
        
                    image_aft = cv2.imread(image_path_aft) # 画像ファイル読み込み
                    gray = cv2.cvtColor(image_aft, cv2.COLOR_BGR2GRAY) # グレースケースに変換
        
                    laplacian_aft = cv2.Laplacian(gray, cv2.CV_64F) #ラプラシアン値
                    
                    #idxの前の探索
                    #最初のフレームは前のidxがないのでi=0
                    if idx==0: bef=0
                    else: bef=i
                    image_path_bef = r_path + image_file[idx-bef]
                    out_image_path = w_path + image_file[idx-bef]
        
                    image_bef = cv2.imread(image_path_bef) # 画像ファイル読み込み
                    gray = cv2.cvtColor(image_bef, cv2.COLOR_BGR2GRAY) # グレースケースに変換
        
                    laplacian_bef = cv2.Laplacian(gray, cv2.CV_64F) #ラプラシアン値
                    
                    #iフレーム前後でラプラシアン値が大きい方を選択
                    lap_dict={'aft':laplacian_aft.var(),'bef':laplacian_bef.var()}
                    lap_key=max(lap_dict,key=lap_dict.get)
                    lap_val=max(lap_dict.values())
                    
                    #ラプラシアン値と前後どちらが選ばれたかの記憶
                    lap_val_list+=[lap_val]
                    lap_key_list+=[lap_key]
                    
                    if lap_val >= 100: # 閾値100以上のピンボケでない画像のみ出力
        
                        #cv2.putText(eval(f'image_{lap_key}'), "{:.2f}".format(lap_val), (10, 30),#ラプラシアン値を表示
                        #    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
                        cv2.imwrite(out_image_path, eval(f'image_{lap_key}'))
                        output_cnt+=1
                        break
                        
                if output_cnt==0:#前後5フレームでブラーなし画像が１つも無ければ、その中でラプラシアン値が最大のものを出力
                    max_idx=lap_val_list.index(max(lap_val_list))#記憶リストの中でラプラシアン値最大のidx
                    max_key=lap_key_list[max_idx]#その時の前後どちらだったか
                    if max_key=='bef': max_idx=-max_idx#前だったらそのidx分、現在のidxから引く
                    
                    image = cv2.imread(r_path + image_file[idx+max_idx]) # 画像ファイル読み込み
                    #cv2.putText(image, "{:.2f}".format(max(lap_val_list)), (10, 30),#ラプラシアン値の表示
                    #        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
                    cv2.imwrite(w_path + image_file[idx+max_idx], image)
                    #print('b',i,image_file[idx])
                    
    
if __name__=='__main__':
    
    num_photo_dir=save_frame_range_sec(video_path, photo_path, start_sec, stop_sec, basename, fps)

    select_high_laplacian(photo_path,selected_path,num_photo_dir)
       




