{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    (python3.withPackages (ps: with ps; [
      pygame
      numpy  # Для генерации звуков, если нужно
    ]))

    # SDL и зависимости
    SDL2
    SDL2_image
    SDL2_mixer
    SDL2_ttf
    
    # Аудио-зависимости
    alsa-lib
    libpulseaudio
    fluidsynth  # Для MIDI поддержки
    
    # Графические зависимости
    glib
    zlib
    libGL
    xorg.libX11
    xorg.libXext
    xorg.libXrender
    xorg.libXinerama
    xorg.libXcursor
    xorg.libXi
    xorg.libXrandr
    xorg.libXfixes
    freetype
    fontconfig
    
    # Системные библиотеки
    stdenv.cc.cc.lib
  ];

  shellHook = ''
    # Установка переменных окружения для звука
    export SDL_AUDIODRIVER="pulse"  # Или "alsa" если pulseaudio не работает
    
    # Пути к библиотекам
    export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [
      pkgs.glib
      pkgs.zlib
      pkgs.SDL2
      pkgs.SDL2_mixer
      pkgs.SDL2_image
      pkgs.SDL2_ttf
      pkgs.libGL
      pkgs.xorg.libX11
      pkgs.xorg.libXext
      pkgs.xorg.libXrender
      pkgs.freetype
      pkgs.fontconfig
      pkgs.alsa-lib
      pkgs.libpulseaudio
      pkgs.fluidsynth
      pkgs.stdenv.cc.cc.lib
    ]}:$LD_LIBRARY_PATH

    export PYTHONPATH=${pkgs.python3.pkgs.pygame}/lib/python3.*/site-packages:$PYTHONPATH
    
    echo "Аудио драйвер для SDL: $SDL_AUDIODRIVER"
    ${pkgs.pulseaudio}/bin/pactl list sinks | grep -E 'Name|Description' || echo "PulseAudio не доступен"
  '';
}