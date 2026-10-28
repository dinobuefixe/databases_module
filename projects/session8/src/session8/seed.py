from session8.connection import get_engine, get_inputs_connstr, get_insights_connstr
from session8.models import inputs, insights

from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    # Example usage
    inputs_engine = get_engine(get_inputs_connstr())

    inputs.Base.metadata.create_all(inputs_engine)

    insights_engine = get_engine(get_insights_connstr())

    insights.Base.metadata.create_all(insights_engine)