from kerykeion import AstrologicalSubject, RelationshipScoreFactory


class TestRelationshipScore:
    def setup_class(self):
        self.john_lennon = AstrologicalSubject("John", 1940, 10, 9, 18, 30, "Liverpool", "UK")
        self.yoko_ono = AstrologicalSubject("Yoko", 1933, 2, 18, 20, 30, "Tokyo", "JP")

        self.freud = AstrologicalSubject("Freud", 1856, 5, 6, 18, 30, "Freiberg", "DE")
        self.jung = AstrologicalSubject("Jung", 1875, 7, 26, 18, 30, "Kesswil", "CH")

        self.richart_burton = AstrologicalSubject("Richard Burton", 1925, 11, 10, 15, 00, "Pontrhydyfen", "UK")
        self.liz_taylor = AstrologicalSubject("Elizabeth Taylor", 1932, 2, 27, 2, 30, "London", "UK")

        self.dario_fo = AstrologicalSubject("Dario Fo", 1926, 3, 24, 12, 25, "Sangiano", "IT")
        self.franca_rame = AstrologicalSubject("Franca Rame", 1929, 7, 18, 12, 25, "Parabiago", "IT")

    def test_john_lennon_yoko_ono_relationship_score(self):
        john_yoko_relationship_score_factory = RelationshipScoreFactory(self.john_lennon, self.yoko_ono)
        john_yoko_relationship_score = john_yoko_relationship_score_factory.get_relationship_score()

        assert john_yoko_relationship_score.score_description == "Very Important"
        assert john_yoko_relationship_score.score_value == 16

    def test_freud_jung_relationship_score(self):
        freud_jung_relationship_score_factory = RelationshipScoreFactory(self.freud, self.jung)
        freud_jung_relationship_score = freud_jung_relationship_score_factory.get_relationship_score()
        
        assert freud_jung_relationship_score.score_description == "Rare Exceptional"
        assert freud_jung_relationship_score.score_value == 32

    def test_richart_burton_liz_taylor_relationship_score(self):
        burton_taylor_relationship_score_factory = RelationshipScoreFactory(self.richart_burton, self.liz_taylor)
        burton_taylor_relationship_score = burton_taylor_relationship_score_factory.get_relationship_score()

        assert burton_taylor_relationship_score.score_description == "Exceptional"
        assert burton_taylor_relationship_score.score_value == 23

    def test_dario_franca_relationship_score(self):
        dario_franca_relationship_score_factory = RelationshipScoreFactory(self.dario_fo, self.franca_rame)
        dario_franca_relationship_score = dario_franca_relationship_score_factory.get_relationship_score()

        assert dario_franca_relationship_score.score_description == "Important"
        assert dario_franca_relationship_score.score_value == 13

if __name__ == "__main__":
    import pytest
    import logging

    # Set the log level to CRITICAL
    logging.basicConfig(level=logging.CRITICAL)
    
    pytest.main(["-vv", "--log-level=CRITICAL", "--log-cli-level=CRITICAL", __file__])