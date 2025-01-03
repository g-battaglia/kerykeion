from kerykeion import KerykeionException
from kerykeion.utilities import is_point_between
import pytest


class TestUtilities:
    
    def setup_class(self):
        pass

    def test_is_point_between(self):
        assert is_point_between(10, 30, 25) is True
        assert is_point_between(10, 30, 35) is False
        assert is_point_between(10, 30, 4) is False

        assert is_point_between(340, 10, 350) is True
        assert is_point_between(340, 10, 4) is True
        assert is_point_between(340, 10, 320) is False
        assert is_point_between(340, 10, 20) is False
        
        # Edge cases
        assert is_point_between(10, 30, 10) is True
        assert is_point_between(10, 30, 30) is False
        
        assert is_point_between(340, 10, 340) is True
        assert is_point_between(340, 10, 10) is False
        
        assert is_point_between(0, 20, 0) is True
        assert is_point_between(0, 20, 20) is False
        
        assert is_point_between(340, 360, 340) is True
        assert is_point_between(340, 360, 360) is False

        assert is_point_between(360, 20, 0) is True
        assert is_point_between(360, 20, 20) is False
        assert is_point_between(360, 20, 360) is True
        
        assert is_point_between(340, 0, 340) is True
        assert is_point_between(340, 0, 0) is False
        assert is_point_between(360, 20, 360) is True
        
        assert is_point_between(10, 30, 10.00000000001) is True
        assert is_point_between(10, 30, 9.999999999999) is False
        assert is_point_between(10, 30, 29.999999999999) is True
        assert is_point_between(10, 30, 30.00000000001) is False
        
        assert is_point_between(97.89789490940346, 116.14575774583493, 97.89789490940348) is True
        assert is_point_between(97.89789490940346, 116.14575774583493, 97.89789490940340) is False
        assert is_point_between(97.89789490940346, 116.14575774583493, 116.14575774583490) is True
        assert is_point_between(97.89789490940346, 116.14575774583493, 116.14575774583496) is False


    def test_is_point_between_with_exception(self):
        with pytest.raises(KerykeionException) as ex:
            is_point_between(5, 200, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")
        
        with pytest.raises(KerykeionException) as ex:    
            is_point_between(250, 200, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")
           
        with pytest.raises(KerykeionException) as ex: 
            is_point_between(0, 180.1, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")
            
        with pytest.raises(KerykeionException) as ex: 
            is_point_between(359.9, 180, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")