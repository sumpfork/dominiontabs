import argparse
from pathlib import Path

from fontTools.ttLib import TTFont
from loguru import logger


def convert_otf_to_ttf(otf_path, ttf_path):
    """Convert OTF (PostScript) to TTF (TrueType) format."""
    font = TTFont(otf_path)
    
    # Check if font has CFF (PostScript outlines)
    if 'CFF ' in font or 'CFF2' in font:
        # Use cu2qu to convert PostScript curves to TrueType
        from cu2qu.pens import Cu2QuPen
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        from fontTools.ttLib.tables import _g_l_y_f, _l_o_c_a
        
        glyph_set = font.getGlyphSet()
        glyph_order = font.getGlyphOrder()
        
        # Create new glyf table
        glyf = _g_l_y_f.table__g_l_y_f()
        glyf.glyphs = {}
        glyf.glyphOrder = glyph_order
        
        # Convert each glyph
        for glyph_name in glyph_order:
            pen = TTGlyphPen(glyph_set)
            cu2qu_pen = Cu2QuPen(pen, max_err=1.0, reverse_direction=True)
            
            # Draw the glyph
            try:
                glyph_set[glyph_name].draw(cu2qu_pen)
                glyf.glyphs[glyph_name] = pen.glyph()
            except Exception as e:
                logger.warning(f"Could not convert glyph '{glyph_name}': {e}")
                # Create empty glyph as fallback
                glyf.glyphs[glyph_name] = _g_l_y_f.Glyph()
        
        # Replace CFF table with glyf/loca
        if 'CFF ' in font:
            del font['CFF ']
        if 'CFF2' in font:
            del font['CFF2']
            
        font['glyf'] = glyf
        font['loca'] = _l_o_c_a.table__l_o_c_a()
        
        # CRITICAL: Change sfntVersion from 'OTTO' to '\x00\x01\x00\x00' for TrueType
        font.sfntVersion = "\x00\x01\x00\x00"
        
        # Fix maxp table version (must be 1.0 for TrueType, not 0.5 for CFF)
        if 'maxp' in font:
            maxp = font['maxp']
            if maxp.tableVersion < 0x00010000:
                maxp.tableVersion = 0x00010000
                # Add TrueType-specific maxp fields with reasonable defaults
                maxp.maxZones = 2
                maxp.maxTwilightPoints = 0
                maxp.maxStorage = 0
                maxp.maxFunctionDefs = 0
                maxp.maxInstructionDefs = 0
                maxp.maxStackElements = 0
                maxp.maxSizeOfInstructions = 0
                maxp.maxComponentElements = 0
                maxp.maxComponentDepth = 0
    
    # Save as TTF with TrueType flavor
    font.flavor = None
    font.save(ttf_path)
    font.close()


def main():
    """Main entry point for the fontfix CLI tool."""
    parser = argparse.ArgumentParser(
        description="Convert OTF fonts to TTF format with proper TrueType outlines"
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        default=Path(__file__).parent.parent.parent.parent / "local_fonts",
        help="Directory containing OTF files to convert (default: local_fonts)",
    )
    
    args = parser.parse_args()
    fonts_dir = args.directory
    
    if not fonts_dir.exists():
        logger.error(f"Directory does not exist: {fonts_dir}")
        return 1
    
    if not fonts_dir.is_dir():
        logger.error(f"Not a directory: {fonts_dir}")
        return 1
    
    # Find all .otf files
    otf_files = list(fonts_dir.glob("*.otf"))
    
    logger.info(f"Found {len(otf_files)} OTF files to convert in {fonts_dir}")
    
    # Convert each .otf to .ttf
    for otf_file in otf_files:
        ttf_file = otf_file.with_suffix(".ttf")
        logger.info(f"Converting {otf_file.name} -> {ttf_file.name}")
        
        try:
            convert_otf_to_ttf(str(otf_file), str(ttf_file))
            logger.success(f"Successfully converted {otf_file.name}")
        except Exception as e:
            logger.error(f"Failed to convert {otf_file.name}: {e}")
            logger.exception(e)
    
    logger.info("Conversion complete!")
    return 0


if __name__ == "__main__":
    exit(main())
