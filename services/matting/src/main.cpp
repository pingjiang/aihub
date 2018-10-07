//
//  main.cpp
//  AlphaMatting
//
//  Created by Volvet Zhang on 16/6/15.
//  Copyright © 2016年 Volvet Zhang. All rights reserved.
//

#include <iostream>
#include <string>

#include "SharedMatting.h"

using namespace cv;

int main(int argc, const char * argv[]) {
    if (argc < 3) {
        std::cout << "Usage: matting input.png trimap.png out.png" << std::endl;
        return 1;
    }

    SharedMatting sm;
    sm.loadImage(argv[1]);
    sm.loadTrimap(argv[2]);
    sm.solveAlpha();
    sm.save(argv[3]);
    
    return 0;
}
