#!/usr/bin/env python
# ******************************************************************************
# Copyright (c) 2018 Bentley Systems, Incorporated. All rights reserved.
# ******************************************************************************
# iTwin Capture Modeler Python SDK - example script
#
# Script: import_txt.py
# Purpose : import a custom block format
# Keywords: block creation, block import, project creation
#
# Script description:
# - creates a new CCM project,
# - reads a custom block definition from a TXT file, and creates the corresponding block.
# - export block to KML
# ******************************************************************************
import sys
import os
import csv
import itwincapturemodeler
import pandas as pd
import time
import bs4
from distutils.util import strtobool
import shutil

photosDirPath = './selected/'#100個づつに分けた写真フォルダ
photosDir_lists = os.listdir(photosDirPath)
inputFilePath = './LiDAR/results_video_traj.txt'#video軌跡
projectDirPath = './project'#projectが作成されるディレクトリ
zebcamPath = 'F:/zeb-cam.opt'
txtFilePath = './LiDAR/results_traj.txt'
lazFilePath = './LiDAR/withceiling.subsampled.laz'

PHOTO_COL = 9#trajの画像名カラム
X_COL = 0#xカラム
Y_COL = 1#yカラム
Z_COL = 2#zカラム

def main():
    if itwincapturemodeler.edition()!='Center':
        print("edition error %s can not use" % itwincapturemodeler.edition())#Licenceと違うeditionだったら実行しない
        sys.exit(0)
    print('iTwin Capture Modeler version %s' % itwincapturemodeler.version())#バージョン情報
    print('')
    
    if not itwincapturemodeler.isLicenseValid():
        print("License error: ", itwincapturemodeler.lastLicenseErrorMsg())
        sys.exit(0)
    
    # --------------------------------------------------------------------
    # create project
    # --------------------------------------------------------------------
    if os.path.exists(projectDirPath):shutil.rmtree(projectDirPath)#前のプロジェクトディレクトリは削除
    
    projectName = os.path.basename(projectDirPath)#プロジェクト名（パスの中から取得）
    
    project = itwincapturemodeler.Project()#Projectインスタンスを作成
    project.setName(projectName)#プロジェクト名をセット
    project.setDescription('Automatically generated from python script')
    project.setProjectFilePath(os.path.join(projectDirPath, projectName))#プロジェクトのパスを設定
    err = project.writeToFile()#プロジェクトファイルをセーブ（エラーだったらエラーメッセージ）
    if not err.isNone():
        print(err.message)
        sys.exit(0)
    
    print('Project %s successfully created.' % projectName)
    print('')

    SRSManager = project.getProjectSRSManager()
    id=SRSManager.getOrCreateProjectSRSId("","Local coordinate system(meters)")

    rd=pd.read_csv(inputFilePath,header=None, engine='python',sep='  ')#result_video_traj読み込み

    #zeb_cam.optの読み込み
    soup=bs4.BeautifulSoup(open(zebcamPath,encoding='utf-8'),features="html.parser")
    element=soup.find_all('opticalproperties')

    l=[]
    for index in element:
        for i in range(len(index)):
            l+=[index.contents[i].get_text()]
    l=[i for i in l if i!='\n']

    wide=int(l[3].split('\n')[1])
    height=int(l[3].split('\n')[2])
    cameramodeltype=l[4].lower()
    cameramodelband=l[5].lower()
    k1=float(l[6].split('\n')[1])
    k2=float(l[6].split('\n')[2])
    k3=float(l[6].split('\n')[3])
    p1=float(l[6].split('\n')[4])
    p2=float(l[6].split('\n')[5])
    direct=bool(strtobool(l[6].split('\n')[6]))
    focallengthpixel=float(l[7])
    x=float(l[8].split('\n')[1])
    y=float(l[8].split('\n')[2])
    aspectratio=int(l[9])
    skew=int(l[10])

    #Prepare trajectory
    print("Importing trajectories...")
    ff=itwincapturemodeler.FileFormat()
    ff.combineDelimiters = True
    ff.decimalSeparator = '.'
    ff.delimiters = [' ']
    ff.numIgnoredLines = 1
    ff.setNumericField('x', 1)
    ff.setNumericField('y', 2)
    ff.setNumericField('z', 3)
    ff.setNumericField('time', 0)    
    
    trajs = itwincapturemodeler.Trajectories()
    err = trajs.readFromFiles([txtFilePath],ff)
    assert err.isNone(), "Failed to read trajectories from files: " + err.getErrorString() + " [" + err.message + "]"
    #assert trajs.setSRS("epsg:4326"), "Failed to set SRS for Mobile LAS"

    #Import point colud
    print("Importing pointcloud...")
    block=itwincapturemodeler.Block(project)
    project.addBlock(block)
    err = block.importPointCloudFromMobileScans(lazFilePath,"",trajs)

    assert err.isNone(), "Failed to import pointcloud: " + err.getErrorString() + " [" + err.message + "]"
    block.setChanged()
    block.exportToKML(os.path.join(projectDirPath, 'block.kml'))

    err = project.writeToFile()
    if not err.isNone():
        print(err.message)
        sys.exit(0)       

    blockVec=itwincapturemodeler.BlockVec()
    blockVec.append(block)
    
    for photosDir_list in photosDir_lists:#100枚の画像のディレクトリ
        
        # --------------------------------------------------------------------
        # create block(import_txt)
        # --------------------------------------------------------------------
        block=itwincapturemodeler.Block(project)#blockインスタンスを作成
        block.setPositioningLevel(itwincapturemodeler.PositioningLevel.PositioningLevel_absoluteMetric)
        project.addBlock(block)#プロジェクトにブロックを追加
        
        photogroups = block.getPhotogroups()#ブロックのフォトグループへの内部参照を返します
        photogroups.addPhotogroup( itwincapturemodeler.Photogroup() )#空のフォトグループリストを作成してフォトグループを追加
        photogroup = photogroups.getPhotogroup(photogroups.getNumPhotogroups() - 1)#前のコマンドが成功した場合に自動的に追加されます。
        
        # --------------------------------------------------------------------
        # parse input txt file
        # --------------------------------------------------------------------
        firstPhoto = True
        photo_names=os.listdir(os.path.join(photosDirPath, photosDir_list))
    
        for name in photo_names:
            row=rd[rd[PHOTO_COL]==name]#画像名と一致する行
            inputP = itwincapturemodeler.Point3d(float(row.iloc[0][X_COL]), float(row.iloc[0][Y_COL]), float(row.iloc[0][Z_COL]))#xyz座標取得

            imageFilePath = os.path.join(photosDirPath, photosDir_list, row.iloc[0][PHOTO_COL])
            photo = itwincapturemodeler.Photo(imageFilePath,itwincapturemodeler.ImageDimensions(wide,height))#画像読み込み
            photo.pose.center = inputP
            photo.poseMetadata.srsId = id
            photo.poseMetadata.center = inputP
            
            if firstPhoto:#最初だけ実行
                firstPhoto = False            
                photogroup.setupFromPhoto(photo)
                #写真属性(exif、imageDimensions、directoryPath、DBプロパティ)から属性を初期化します。
    
            photogroup.addPhoto(photo)#フォトグループに画像を追加
       
        photogroup.imgaeDimensions=(wide,height)
        exec(f'photogroup.cameraModelType=itwincapturemodeler.bindings.CameraModelType.CameraModelType_{cameramodeltype}')
        exec(f'photogroup.cameraModelBand=itwincapturemodeler.bindings.CameraModelBand.CameraModelBand_{cameramodelband}')
        photogroup.distortion=itwincapturemodeler.Distortion(k1,k2,k3,p1,p2,direct)
        photogroup.setFocalLength_px(focallengthpixel)
        photogroup.principalPoint=itwincapturemodeler.Point2d(x,y)
        photogroup.aspectRatio=aspectratio
        photogroup.skew=skew
       
        block.setChanged()
        #ブロックが内部的に変更されたことを警告するために、ブロックを直接変更した後に呼び出す必要があるため、次のプロジェクトの保存でブロックが確実に保存されるようにします。
        block.exportToKML(os.path.join(projectDirPath, 'block.kml'))
        #視覚化に適した KML 図面に写真の位置を書き出します

        err = project.writeToFile()#プロジェクトの保存
        if not err.isNone():
            print(err.message)
            sys.exit(0)       

        # --------------------------------------------------------------------
        # AT
        # --------------------------------------------------------------------
        blockAT=itwincapturemodeler.Block(project)
        project.addBlock(blockAT)
        blockAT.setBlockTemplate(itwincapturemodeler.BlockTemplate.Template_adjusted, block)
    
        err = project.writeToFile()
        if not err.isNone():
            print(err.message)
            sys.exit(0)
    
        # Set some settings
        at_settings = blockAT.getAT().getSettings()
        at_settings.keyPointsDensity = itwincapturemodeler.KeyPointsDensity.KeyPointsDensity_high
        at_settings.splatsPreprocessing = itwincapturemodeler.SplatsPreprocessing.SplatsPreprocessing_none
        
        if not blockAT.getAT().setSettings(at_settings):
            print("Error: Failed to set settings for aerotriangulation")
            sys.exit(0)
        atSubmitError = blockAT.getAT().submitProcessing()
    
        if not atSubmitError.isNone():
            print('Error: Failed to submit aerotriangulation.')
            print(atSubmitError.message)
            sys.exit(0)

        #at_settings.adjustmentConstraints = itwincapturemodeler.bindings.PositioningMode.PosMode_adjustmentFromGPSTags#####
        #at_settings.adjustmentConstraints = itwincapturemodeler.bindings.PositioningMode.PosMode_automatic
        
        print('The aerotriangulation job has been submitted and is waiting to be processed...')
    
        iPreviousProgress = 0
        iProgress = 0
        previousJobStatus = itwincapturemodeler.JobStatus.Job_unknown
        jobStatus = itwincapturemodeler.JobStatus.Job_unknown
    
        while 1:
            jobStatus = blockAT.getAT().getJobStatus()
    
            if jobStatus != previousJobStatus:
                print(itwincapturemodeler.jobStatusAsString(jobStatus))
    
            if jobStatus == itwincapturemodeler.JobStatus.Job_failed or jobStatus == itwincapturemodeler.JobStatus.Job_cancelled or jobStatus == itwincapturemodeler.JobStatus.Job_completed:
                break
    
            if iProgress != iPreviousProgress:
                print('%s%% - %s' % (iProgress,blockAT.getAT().getJobMessage()))
    
            iPreviousProgress = iProgress
            iProgress = blockAT.getAT().getJobProgress()
            time.sleep(1)
            blockAT.getAT().updateJobStatus()
            previousJobStatus = jobStatus
    
        if jobStatus != itwincapturemodeler.JobStatus.Job_completed:
            print('"Error: Incomplete aerotriangulation.')
    
            if blockAT.getAT().getJobMessage() != '':
                print( blockAT.getAT().getJobMessage() )
    
        print('Aerotriangulation completed.')
    
        if not blockAT.canGenerateQualityReport():
            print("Error: BlockAT can't generate Quality report")
            sys.exit(0)
    
        if not blockAT.generateQualityReport(True):
            print("Error: failed to generate Quality report")
            sys.exit(0)
    
        print("AT report available at", blockAT.getQualityReportPath())
    
        if  not blockAT.isReadyForReconstruction():
            print('Error: Incomplete photos. Cannot create reconstruction.')
            sys.exit(0)
    
        print('Ready for reconstruction.')
    
        if blockAT.getPhotogroups().getNumPhotosWithCompletePose_byComponent(1) < blockAT.getPhotogroups().getNumPhotos():
            print('Warning: incomplete photos. %s/%s photo(s) cannot be used for reconstruction.' % ( blockAT.getPhotogroups().getNumPhotos() - blockAT.getPhotogroups().getNumPhotosWithCompletePose_byComponent(1), blockAT.getPhotogroups().getNumPhotos() ) );

        blockVec.append(blockAT)

        err = project.writeToFile()#プロジェクトの保存
        if not err.isNone():
            print(err.message)
            sys.exit(0)       

    project.mergeBlocks(blockVec)
    block=project.getBlock(project.getNumBlocks()-1)

    err = project.writeToFile()#プロジェクトの保存
    if not err.isNone():
        print(err.message)
        sys.exit(0)       

    if(0):
        # --------------------------------------------------------------------
        # create reconstruction
        # --------------------------------------------------------------------
        reconstruction = itwincapturemodeler.Reconstruction(block)
        block.addReconstruction(reconstruction)
    
        reconstruction.setDescription('Automatically generated from python script')
    
        # ------
        # Tiling
        # ------
        tiling = reconstruction.getTiling()
        tiling.tilingMode = itwincapturemodeler.TilingMode.TilingMode_regularPlanarGrid
        tiling.tileSize = 5
        #tiling.customOrigin = itwincapturemodeler.Point3d(651500, 6861500, 0)
        tiling.autoOrigin = True
    
        reconstruction.setTiling(tiling)
    
        # -------------------
        # Processing settings
        # -------------------
        settings = reconstruction.getSettings()
        
        settings.geometryPrecisionMode = itwincapturemodeler.GeometryPrecisionMode.GeometryPrecision_extra
        
        #settings.holeFillingMode = itwincapturemodeler.HoleFillingMode.HoleFilling_allHoles
        
        settings.holeFillingMode = itwincapturemodeler.HoleFillingMode.HoleFilling_smallHoles
        
        #settings.pairSelectionMode = itwincapturemodeler.ReconstructionPairSelectionMode.ReconstructionPairSelection_forStructuredAerialDataset
        
        settings.pairSelectionMode = itwincapturemodeler.ReconstructionPairSelectionMode.ReconstructionPairSelection_generic
        
        settings.photosUsedForGeometry   = itwincapturemodeler.ReconstructionPhotosUsedForGeometry.ReconstructionPhotosUsedForGeometry_none
    
        reconstruction.setSettings(settings)
    
        print(vars(settings))
        block.setChanged()
    
        # --------------------------------------------------------------------
        # Save project
        # --------------------------------------------------------------------
        err = project.writeToFile()
        if not err.isNone():
            print(err.message)
            sys.exit(0)
    
        # --------------------------------------------------------------------
        # Display actual reconstruction settings
        # --------------------------------------------------------------------
        print()
        print('Reconstruction settings:')
    
        print('Tiling:')
        tiling = reconstruction.getTiling()
        print('-Mode:', tiling.tilingMode)
        print('-TileSize:', tiling.tileSize)
    
        # if tiling.customOrigin:
        #     print('-CustomOrigin: (%s,%s,%s)' % (tiling.customOrigin.x, tiling.customOrigin.y, tiling.customOrigin.z))
    
        print()
    
        print('Processing settings:')
        settings = reconstruction.getSettings()
        print('-Geometry precision mode:', settings.geometryPrecisionMode)
        print('-Hole filling mode:', settings.holeFillingMode)
        print('-Pair selection mode:', settings.pairSelectionMode)
    
        print()
        print('Number of tiles:', reconstruction.getNumInternalTiles())
    
        # define a production for one tile
        production = itwincapturemodeler.Production(reconstruction)
        reconstruction.addProduction(production)
        
        # set production format and destination
        production.setDriverName('OBJ')
        production.setDestination(projectDirPath)
        
        # set production options
        driverOptions = production.getDriverOptions()
        driverOptions.put_int('TextureCompressionQuality', 100)
        production.setDriverOptions(driverOptions)
        
        # sumbit production processing
        production.submitProcessing()
    
if __name__ == '__main__':
    main()
