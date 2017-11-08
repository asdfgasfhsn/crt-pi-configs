# creates cfg files for crt-pi
# params are:
# * core (eg mame2003 or fbalpha)
# * screen width (eg 1920) OR curvature
# * screen height (eg 1080)
# example usage:
# python crt_pi_configs.py mame2003 1920 1080
# python crt_pi_configs.py fbalpha 1920 1080
# python crt_pi_configs.py consoles 1920 1080
# python -c "import crt_pi_configs; crt_pi_configs.createZip(False,1920,1080)"

import sys
import os
import shutil


def generateConfigs(arg1, arg2, arg3):
    console = False
    if "mame2003" in arg1:
        fileName = "resolution_db/mame2003.txt"
        coreName = "MAME 2003"
    elif "fbalpha" in arg1:
        fileName = "resolution_db/fbalpha.txt"
        coreName = "FB Alpha"
    elif "consoles" in arg1:
        fileName = "resolution_db/consoles.txt"
        console = True

    if "curvature" in arg2:
        curvature = True
    else:
        curvature = False
        screenWidth = int(arg2)
        screenHeight = int(arg3)
        screenAspectRatio = screenWidth / screenHeight
        tolerance = 25
        resolution = str(screenWidth) + "x" + str(screenHeight)
        outputLogFile = open(coreName + "-" + resolution + ".csv", "w")
        outputLogFile.write("Tolerance : ,{}\n".format(tolerance))
        outputLogFile.write("ROM Name,X,Y,Orientation,Aspect1,Aspect2,ViewportWidth,ViewportHeight,HorizontalOffset,VerticalOffset\n")

    resolutionDbFile = open(fileName, "r" )
    print("Opened database file {}".format(fileName))
    if not curvature:
        print("created log file ./{}".format(outputLogFile.name))
    print("Creating system-specific config files.\n")
    sys.stdout.write('[')
    sys.stdout.flush()
    gameCount = 0

    for gameInfo in resolutionDbFile:
        gameCount = gameCount+1
    	# strip line breaks
        gameInfo = gameInfo.rstrip()
        
        # parse info
        gameInfo = gameInfo.split(",")
        gameName = gameInfo[0]
        gameOrientation = gameInfo[3]
        gameWidth = int(gameInfo[1])
        gameHeight = int(gameInfo[2])
        aspectRatio = int(gameInfo[9]) / int(gameInfo[10])
        gameType = gameInfo[4]
        #integerWidth = int(gameInfo[7])
        #integerHeight = int(gameInfo[8])

        if console:
            coreName = gameName

        cfgFileName = gameName + ".cfg"

        # Create directory for cfgs, if it doesn"t already exist
        if curvature:
            path = "curvature" + "/" + coreName
        else:
            path = resolution + "/" + coreName
        if not os.path.isdir(path):
            os.makedirs (path)

        # create cfg file
        if (gameCount%100 == 0):
            sys.stdout.write('.')
            sys.stdout.flush()
        newCfgFile = open(path + "/" + cfgFileName, "w")

        if "V" in gameType:
            # Vector games shouldn"t use shaders, so clear it out
            newCfgFile.write("# Auto-generated vector .cfg\n")
            newCfgFile.write("# Place in /opt/retropie/configs/all/retroarch/config/{}/\n".format(coreName))
            newCfgFile.write("video_shader_enable = \"false\"\n")

        else:
            if "V" in gameOrientation:
                if curvature:
                    shader = "crt-pi-curvature-vertical.glslp"
                else:
                    shader = "crt-pi-vertical.glslp"
                # flip vertical games
                gameWidth = int(gameInfo[2])
                gameHeight = int(gameInfo[1])

            elif "H" in gameOrientation:
                if curvature:
                    shader = "crt-pi-curvature.glslp"
                else:
                    shader = "crt-pi.glslp"

            newCfgFile.write("# Auto-generated {} .cfg\n".format(shader))
            newCfgFile.write("# Game Title : {} , Width : {}, Height : {}, Aspect : {}:{}\n".format(gameName, gameWidth, gameHeight, int(gameInfo[9]), int(gameInfo[10])))
            if not curvature:
                newCfgFile.write("# Screen Width : {}, Screen Height : {}\n".format(screenWidth, screenHeight))
            newCfgFile.write("# Place in /opt/retropie/configs/all/retroarch/config/{}/\n".format(coreName))
            newCfgFile.write("video_shader_enable = \"true\"\n")
            newCfgFile.write("video_shader = \"/opt/retropie/configs/all/retroarch/shaders/{}\"\n".format(shader))

            if not curvature:
                # if not perfectly integer scaled, we will get scaling artefacts, so let's fix that
                if screenAspectRatio >= aspectRatio:
                    # games with an aspect ratio smaller than your screen should be scaled to fit vertically
                    newCfgFile.write("# To avoid horizontal rainbow artefacts, use integer scaling for the width\n")

                    # build list of potential aspect ratios with different integer scales
                    aspectRatios = []
                    for scaleX in range(1, 99):
                        aspectRatios.append((scaleX * gameWidth) / screenHeight)

                    # find closest integer scale to desired ratio
                    aspectRatios.reverse()
                    scaleX = 98-aspectRatios.index(min(aspectRatios, key=lambda x:abs(x-aspectRatio)))

                    viewportWidth = int(gameWidth * scaleX)
                    # careful not to exceed screen height
                    if viewportWidth > screenWidth:
                        viewportWidth = int(gameWidth * (scaleX - 1))

                    if console:
                        # consoles have overscan, so adjust viewportHeight to "Title Safe Area"
                        if "Nestopia" in coreName:
                            overscanV = 8
                        else:
                            overscanV = 0

                        # build list of potential aspect ratios with different integer scales
                        aspectRatios = []
                        for scaleY in range(1, 99):
                            aspectRatios.append(viewportWidth / (scaleY * gameHeight))

                        # find closest integer scale to desired ratio
                        aspectRatios.reverse()
                        scaleY = 98-aspectRatios.index(min(aspectRatios, key=lambda x:abs(x-aspectRatio)))

                        viewportHeight = screenHeight + (overscanV * scaleY)
                    else:
                        viewportHeight = screenHeight

                    # we prefer it to be wider than narrower, so do that, according to tolerance
                    newAspect = viewportWidth / viewportHeight
                    if newAspect < aspectRatio:
                        # careful not to exceed screen width
                        if ((scaleX + 1) * gameWidth) <= screenWidth:
                            widerAspect = (gameWidth * (scaleX + 1)) / screenHeight
                            if ((widerAspect - aspectRatio)/aspectRatio * 100) <= tolerance:
                                viewportWidth = int(gameWidth * (scaleX + 1))

                else:
                    # games with an aspect ratio larger than your screen should be scaled to fit horizontally
                    newCfgFile.write("# To avoid horizontal rainbow artefacts, use integer scaling for the height\n")
                    
                    # build list of potential aspect ratios with different integer scales
                    aspectRatios = []
                    for scaleY in range(1, 99):
                        aspectRatios.append(screenWidth / (scaleY * gameHeight))

                    # find closest integer scale to desired ratio
                    aspectRatios.reverse()
                    scaleY = 98-aspectRatios.index(min(aspectRatios, key=lambda x:abs(x-aspectRatio)))

                    viewportWidth = screenWidth
                    viewportHeight = int(gameHeight * scaleY)

                    # careful not to exceed screen height
                    if viewportHeight > screenHeight:
                        viewportHeight = int(gameHeight * (scaleY - 1))
                    
                # centralise the image
                viewportX = int((screenWidth - viewportWidth) / 2)
                viewportY = int((screenHeight - viewportHeight) / 2)

                newCfgFile.write("aspect_ratio_index = \"22\"\n")
                newCfgFile.write("custom_viewport_width = \"{}\"\n".format(viewportWidth))
                newCfgFile.write("custom_viewport_height = \"{}\"\n".format(viewportHeight))
                newCfgFile.write("custom_viewport_x = \"{}\"\n".format(viewportX))
                newCfgFile.write("custom_viewport_y = \"{}\"\n".format(viewportY))
                
                outputLogFile.write("{},{},{},{},{},{},{},{},{},{}\n".format(gameInfo[0],gameInfo[1],gameInfo[2],gameInfo[3],gameInfo[9],gameInfo[10],viewportWidth,viewportHeight,viewportX,viewportY))

        newCfgFile.close()

    resolutionDbFile.close()
    print("]\n")
    print("Done!\n")
    if not curvature:
        outputLogFile.close()
        print("Log written to ./{}  <--Delete if not needed".format(outputLogFile.name))
    print("Files written to ./{}/\nPlease transfer files to /opt/retropie/configs/all/retroarch/config/{}/\n".format(path, coreName))


def createZip(curvature=False, screenWidth=0, screenHeight=0):
    if curvature:
        outputFileName = "crt-pi-curvature_configs"
        path = "curvature"
    else:
        resolution = str(screenWidth) + "x" + str(screenHeight)
        outputFileName = "crt-pi_configs_" + resolution
        path = resolution
    outputFileName = outputFileName.replace(" ", "")
    outputFileName = outputFileName.lower()

    print("Creating zipfile {}".format(outputFileName))
    shutil.make_archive(outputFileName, "zip", path)

    # now delete config dirs
    print("Deleting temp directory: {}".format(path))
    shutil.rmtree(path)


if __name__ == "__main__":
    # check for Python 3. probably should just make code python 2 + 3 friendly, but...effort
    if sys.version_info[0] < 3:
        raise "Must be using Python 3"
    
    generateConfigs(sys.argv[1], sys.argv[2], sys.argv[3])
